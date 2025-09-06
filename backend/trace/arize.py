from phoenix.otel import register
import logging

# Configure logging to reduce noise
logging.getLogger("opentelemetry").setLevel(logging.WARNING)

# Register Phoenix with selective instrumentation (disable auto_instrument to prevent GeneratorExit issues)
tracer_provider = register(
  project_name="learned",
  endpoint="http://localhost:6006/v1/traces",
  auto_instrument=False  # Disable auto-instrumentation to prevent interference with async generators
)
