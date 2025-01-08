#!/bin/bash

# Install ngrok
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
	| sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
	&& echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
	| sudo tee /etc/apt/sources.list.d/ngrok.list \
	&& sudo apt update \
	&& sudo apt install ngrok

# Setup auth token for ngrok
ngrok config add-authtoken 2oEqLJcdUnNAqdsGu4rFTqz218F_3JoRWiqGDwPrkY4fzeKhN

# Start ngrok
ngrok http http://localhost:5000
