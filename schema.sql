--
-- PostgreSQL database dump
--

-- Dumped from database version 16.9 (Ubuntu 16.9-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.9 (Ubuntu 16.9-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO postgres;

--
-- Name: chat_messages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.chat_messages (
    id uuid NOT NULL,
    thread_id uuid,
    role character varying,
    content text,
    message_type character varying,
    file_url character varying,
    file_name character varying,
    file_type character varying,
    tool_calls text,
    tool_results text,
    sources text,
    created_at character varying
);


ALTER TABLE public.chat_messages OWNER TO postgres;

--
-- Name: chat_threads; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.chat_threads (
    id uuid NOT NULL,
    title character varying,
    project_id uuid,
    user_id character varying,
    created_at character varying,
    updated_at character varying
);


ALTER TABLE public.chat_threads OWNER TO postgres;

--
-- Name: checkpoint_blobs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.checkpoint_blobs (
    thread_id text NOT NULL,
    checkpoint_ns text DEFAULT ''::text NOT NULL,
    channel text NOT NULL,
    version text NOT NULL,
    type text NOT NULL,
    blob bytea
);


ALTER TABLE public.checkpoint_blobs OWNER TO postgres;

--
-- Name: checkpoint_migrations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.checkpoint_migrations (
    v integer NOT NULL
);


ALTER TABLE public.checkpoint_migrations OWNER TO postgres;

--
-- Name: checkpoint_writes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.checkpoint_writes (
    thread_id text NOT NULL,
    checkpoint_ns text DEFAULT ''::text NOT NULL,
    checkpoint_id text NOT NULL,
    task_id text NOT NULL,
    idx integer NOT NULL,
    channel text NOT NULL,
    type text,
    blob bytea NOT NULL,
    task_path text DEFAULT ''::text NOT NULL
);


ALTER TABLE public.checkpoint_writes OWNER TO postgres;

--
-- Name: checkpoints; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.checkpoints (
    thread_id text NOT NULL,
    checkpoint_ns text DEFAULT ''::text NOT NULL,
    checkpoint_id text NOT NULL,
    parent_checkpoint_id text,
    type text,
    checkpoint jsonb NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb NOT NULL
);


ALTER TABLE public.checkpoints OWNER TO postgres;

--
-- Name: knowledge_items; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.knowledge_items (
    id uuid NOT NULL,
    project_id uuid,
    video_id uuid,
    content text,
    source_url character varying,
    source_type character varying,
    processing_status character varying,
    embedding_model character varying,
    task_id character varying,
    processed_at character varying,
    created_at character varying
);


ALTER TABLE public.knowledge_items OWNER TO postgres;

--
-- Name: projects; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.projects (
    id uuid NOT NULL,
    name character varying,
    description text,
    created_at character varying,
    prompt_context text
);


ALTER TABLE public.projects OWNER TO postgres;

--
-- Name: videos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.videos (
    id uuid NOT NULL,
    youtube_id character varying,
    title character varying,
    url character varying,
    transcript text,
    description text,
    project_id uuid,
    duration integer,
    upload_date character varying,
    views integer,
    thumbnail_url character varying,
    processing_status character varying,
    processed_at character varying,
    channel character varying,
    channel_id character varying,
    created_at character varying,
    summary text,
    summary_processing_status character varying DEFAULT 'pending'::character varying,
    summary_processed_at character varying
);


ALTER TABLE public.videos OWNER TO postgres;

--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: chat_messages chat_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_pkey PRIMARY KEY (id);


--
-- Name: chat_threads chat_threads_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_threads
    ADD CONSTRAINT chat_threads_pkey PRIMARY KEY (id);


--
-- Name: checkpoint_blobs checkpoint_blobs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.checkpoint_blobs
    ADD CONSTRAINT checkpoint_blobs_pkey PRIMARY KEY (thread_id, checkpoint_ns, channel, version);


--
-- Name: checkpoint_migrations checkpoint_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.checkpoint_migrations
    ADD CONSTRAINT checkpoint_migrations_pkey PRIMARY KEY (v);


--
-- Name: checkpoint_writes checkpoint_writes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.checkpoint_writes
    ADD CONSTRAINT checkpoint_writes_pkey PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx);


--
-- Name: checkpoints checkpoints_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.checkpoints
    ADD CONSTRAINT checkpoints_pkey PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id);


--
-- Name: knowledge_items knowledge_items_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.knowledge_items
    ADD CONSTRAINT knowledge_items_pkey PRIMARY KEY (id);


--
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- Name: videos videos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.videos
    ADD CONSTRAINT videos_pkey PRIMARY KEY (id);


--
-- Name: checkpoint_blobs_thread_id_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX checkpoint_blobs_thread_id_idx ON public.checkpoint_blobs USING btree (thread_id);


--
-- Name: checkpoint_writes_thread_id_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX checkpoint_writes_thread_id_idx ON public.checkpoint_writes USING btree (thread_id);


--
-- Name: checkpoints_thread_id_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX checkpoints_thread_id_idx ON public.checkpoints USING btree (thread_id);


--
-- Name: ix_chat_messages_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_chat_messages_id ON public.chat_messages USING btree (id);


--
-- Name: ix_chat_threads_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_chat_threads_id ON public.chat_threads USING btree (id);


--
-- Name: ix_knowledge_items_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_knowledge_items_id ON public.knowledge_items USING btree (id);


--
-- Name: ix_projects_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_projects_id ON public.projects USING btree (id);


--
-- Name: ix_projects_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_projects_name ON public.projects USING btree (name);


--
-- Name: ix_videos_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_videos_id ON public.videos USING btree (id);


--
-- Name: ix_videos_title; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_videos_title ON public.videos USING btree (title);


--
-- Name: ix_videos_url; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_videos_url ON public.videos USING btree (url);


--
-- Name: ix_videos_youtube_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_videos_youtube_id ON public.videos USING btree (youtube_id);


--
-- Name: chat_messages chat_messages_thread_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_thread_id_fkey FOREIGN KEY (thread_id) REFERENCES public.chat_threads(id);


--
-- Name: chat_threads chat_threads_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_threads
    ADD CONSTRAINT chat_threads_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- Name: knowledge_items knowledge_items_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.knowledge_items
    ADD CONSTRAINT knowledge_items_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- Name: knowledge_items knowledge_items_video_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.knowledge_items
    ADD CONSTRAINT knowledge_items_video_id_fkey FOREIGN KEY (video_id) REFERENCES public.videos(id);


--
-- Name: videos videos_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.videos
    ADD CONSTRAINT videos_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- PostgreSQL database dump complete
--

