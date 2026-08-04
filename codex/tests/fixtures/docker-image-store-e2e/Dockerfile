FROM scratch
ARG RELEASE_ID
LABEL com.aisoft.e2e.release-id=$RELEASE_ID
COPY server /server
USER 65532:65532
EXPOSE 8080
ENTRYPOINT ["/server"]
