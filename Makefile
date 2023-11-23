run:
	poetry run python -m dswav

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