FROM alpine:3.21
RUN apk add --no-cache openssh-client
RUN adduser -D -u 1000 teacher
ENTRYPOINT ["ssh"]
