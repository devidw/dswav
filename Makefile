.PHONY: dev
dev:
	poetry run python -m dswav

.PHONY: stt
stt:
	whisper \
		--output_format json \
		--output_dir $(OUT_DIR)\
		--model tiny \
		--language $(LANG) \
		--word_timestamps=True \
		--prepend_punctuations=True \
		--append_punctuations=True \
		$(FILE)

.PHONY: docker_build
docker_build:
	docker build \
		-t ghcr.io/devidw/dswav:latest \
		.

.PHONY: docker_push
docker_push:
	docker push \
		ghcr.io/devidw/dswav:latest

.PHONY: docker_run
docker_run:
	-docker stop dswav
	-docker rm dswav
	docker run \
		-d \
		--name dswav \
		-p 7860:7860 \
		-v ./projects:/app/projects \
		ghcr.io/devidw/dswav:latest
	docker logs -f dswav