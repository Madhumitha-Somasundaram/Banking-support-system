FROM public.ecr.aws/aws-observability/aws-otel-collector:latest

COPY config.yaml /etc/otel/config.yaml

CMD ["--config=/etc/otel/config.yaml"]