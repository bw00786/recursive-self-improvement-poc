# Observability

A trace records the end-to-end path of one request; it is composed of spans,
where each span is a timed operation with attributes. OpenTelemetry is a
vendor-neutral standard for traces, metrics, and logs, and its SDK exports
spans to backends such as Jaeger or Langfuse.

Instrumenting LLM calls means recording the model name, prompt, token counts,
latency, and errors on each span. A red action filter strips secrets from
span attributes before export so credentials never reach the tracing backend.
