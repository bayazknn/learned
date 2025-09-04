import textwrap

def get_summary_prompt(description: str | None, transcript: str) -> str:
    """
    Generates the prompt for the Summary Agent.

    Args:
        description: The video description..
        transcript: The full transcript of a video.

    Returns:
        The formatted prompt for the Summary Agent.
    """
    return f"""
You are an expert AI assistant tasked with converting raw YouTube video transcripts into a structured, professional, and information-dense document. This document should serve as a comprehensive technical paper or article, making the information highly discoverable and useful for a Retrieval-Augmented Generation (RAG) system.

**Input:** A raw transcript from a YouTube video, 

**Task:**

1.  **Analyze and Structure:** Read the entire transcript to understand the main topic, key concepts, and logical flow. Identify distinct sections such as introduction, background, core methods, results, conclusion, and any supplementary information.

2.  **Rewrite and Refine:**
    * Eliminate conversational filler words, repeated phrases, and irrelevant tangents.
    * Correct any grammatical errors or awkward phrasing typical of spoken language.
    * Maintain the core meaning and technical accuracy of the original content.
    * Rewrite sentences to be more concise and formal.

3.  **Enhance Detail:** For each section, go beyond a simple summary. **Elaborate on the key points, provide additional context, and synthesize related information from the transcript to create a thorough and detailed explanation.** Your goal is to make each section a comprehensive resource on its own.

4.  **Format the Output:** Organize the content using the following template. Ensure that each section is clearly labeled and contains relevant, expanded information extracted from the transcript. If a section is not applicable, you may omit it or state that the information was not present.

---

### **1.0 Introduction**
* Provide a comprehensive background on the topic.
* Clearly state the purpose of the paper and the problem it addresses.
* Introduce all key concepts and the overall scope of the work that will be covered in subsequent sections. This introduction should set the stage thoroughly.

### **2.0 Background/Problem Statement**
* Provide an in-depth explanation of the context or problem the video addresses.
* Detail any fundamental concepts or prior knowledge necessary to understand the main topic.
* **Expand on this section to include all relevant historical context, existing solutions, and the specific challenges that the project or insight aims to overcome.** This section should be a complete review of the background information.

### **3.0 Methods/Implementation/Technical Details**
* This is the core of the technical paper.
* Describe the step-by-step process, methodology, or implementation discussed in the video in meticulous detail.
* Use numbered or bulleted lists to break down complex procedures.
* **For each step or component, provide an expanded explanation of how it works, why it is used, and what its specific function is within the larger system.**
* Use **bolded text** for key terms and concepts (e.g., **gradient descent**, **transformer architecture**).

### **4.0 Results/Case Study/Insights**
* Present the outcomes, results, or insights from the project/tutorial in detail.
* If the video provides a project demo or feedback, provide a detailed description of the observed behavior, performance metrics (if any), or user feedback.
* **Elaborate on the significance of the results and how they validate the methods or ideas presented.**

### **5.0 Discussion/Analysis**
* Provide a thorough analysis of the results.
* **Discuss the implications, trade-offs, and future potential of the insights presented.**
* Mention any limitations, challenges encountered, or alternative approaches discussed in the video. This section should be a thoughtful and critical examination of the topic.

### **6.0 Conclusion**
* Provide a comprehensive summary of the main points of the paper.
* Reiterate the key takeaways and reinforce the central message.
* **Expand on the potential future work or next steps suggested in the video, explaining what they could entail.**

**Guidelines for the Final Output:**
* **Do not include conversational phrases** or any personal commentary.
* **Focus on clarity and depth.** Every sentence should contribute to the information flow and provide new details.
* The output must be pure text, formatted with headings, subheadings, and lists as requested. No images, tables, or non-textual elements.
* Maintain a consistent, professional tone throughout the document.

                           



**Begin the task using the following raw transcript:**

{transcript}       
"""


def get_query_prompt(user_query: str, summaries: list[str]) -> str:
    """
    Generates the prompt for the Query Agent.

    Args:
        user_query: The original user's query.
        summaries: A list of summaries from one or more videos.

    Returns:
        The formatted prompt for the Query Agent.
    """
    formatted_summaries = "\n".join([f"• {s}" for s in summaries])
    return f"""
    Generate 6 search queries, one on each line, related to the following input query and context:"
                      
    ## Query: 
    {user_query}

    ## Context:
    {summaries}
    """


def get_chatbot_prompt(user_query: str, retrieved_context: str) -> str:
    """
    Generates the prompt for the Chatbot Agent.

    Args:
        user_query: The original user's query.
        retrieved_context: The text retrieved by the RAG system.
        chat_history: (Optional) The history of the conversation.

    Returns:
        The formatted prompt for the Chatbot Agent.
    """
    return f"""
        Summarize the context which are parts of youtube video transcripts.
        Summarize considering the user query to give insight about context.

        ## User Query: 
        {user_query}

        ## Context:
        {retrieved_context}
    """

def get_resource_extraction_prompt(video_description: str) -> str:
    """
    Generates the prompt for extracting resources from video descriptions.

    Args:
        video_description: The video description text to analyze for resources.

    Returns:
        The formatted prompt for resource extraction.
    """
    return f"""
You are an expert AI assistant specialized in extracting educational and research resources from video descriptions. Your task is to identify and extract valuable external resources mentioned in the video description, such as research papers, articles, websites, tools, and other learning materials.

**IMPORTANT RULES:**
1. **EXCLUDE YouTube sponsor links** - Do not extract any links that appear to be sponsorships, advertisements, or promotional content for YouTube creators/channels
2. **Capture article titles even without direct links** - If an article or paper is mentioned by title, extract it even if no URL is provided
3. **Focus on educational/research content** - Prioritize academic papers, research articles, documentation, tutorials, and learning resources
4. **Extract both linked and unlinked resources** - Include resources that have URLs and those that are mentioned by name only
5. **DETECT ARXIV PAPERS WITHOUT LINKS** - Look for academic paper patterns with titles, authors, and affiliations (e.g., "Paper Title... Author1, Author2 from University/Institution")

**Input:** A YouTube video description

**Task:**
Analyze the video description and extract all educational/research resources mentioned. For each resource, provide:

1. **Resource Title/Name**: The title of the article, paper, or resource (required)
2. **URL**: The direct link if provided (optional - can be null if not mentioned)
3. **Resource Type**: Categorize as one of:
   - "paper" - Academic research papers (including arxiv papers)
   - "arxiv-no-link" - Academic papers mentioned without URLs (use this for papers with author/institution format)
   - "article" - Blog posts, news articles, or web articles
   - "documentation" - Official documentation or guides
   - "tutorial" - Educational tutorials or courses
   - "tool" - Software tools, libraries, or applications
   - "website" - Educational websites or platforms
   - "book" - Books or publications
   - "other" - Any other educational resource

**Arxiv Paper Detection Examples:**
Look for patterns like:
- "Dream to Chat: Model-based Reinforcement Learning on Dialogues with User Belief Modeling... Yue Zhao 1, Xiaoyu Wang 1,2, Dan Wang 1... from 1 Geely AI Lab, 2 Beijing Institute of Technology"
- "LSD-3D: Large-Scale 3D Driving Scene Generation with Geometry Grounding... Julian Ost 1, Andrea Ramazzina 2... from 1 Princeton University, 2 Mercedes-Benz"

For these patterns, use "arxiv-no-link" as the resource_type.

**Output Format:**
Return a JSON array of resource objects with the following structure:
[
  {{
    "title": "Resource Title Here",
    "url": "https://example.com/resource" | null,
    "resource_type": "paper|arxiv-no-link|article|documentation|tutorial|tool|website|book|other"
  }}
]

**Guidelines:**
- Only extract resources that are clearly educational or research-oriented
- Skip promotional content, sponsorships, and creator mentions
- If a resource is mentioned multiple times, include it only once
- For resources without URLs, set url to null
- For academic papers with author/institution format but no URL, use "arxiv-no-link"
- Ensure titles are clean and properly formatted
- Focus on quality over quantity - better to miss a resource than include irrelevant content

**Video Description to Analyze:**
{video_description}
"""
