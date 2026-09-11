.PHONY: proxy-setup proxy-enable proxy-disable proxy-status

# 1. Configure and create the proxy in Toxiproxy
proxy-setup:
	@echo "Creating RabbitMQ proxy..."
	curl -s -X POST http://localhost:8474/proxies \
		-H "Content-Type: application/json" \
		-d '{"name": "rabbitmq", "listen": "0.0.0.0:5672", "upstream": "rabbitmq:5672", "enabled": true}'
	@echo "\nProxy configuration completed."

proxy-fix-listen:
	@echo "Updating RabbitMQ proxy listen address to 0.0.0.0..."
	curl -s -X POST http://localhost:8474/proxies/rabbitmq \
		-H "Content-Type: application/json" \
		-d '{"name": "rabbitmq", "listen": "0.0.0.0:5672", "upstream": "rabbitmq:5672", "enabled": true}'
	@echo "\nProxy updated successfully."

# 2. Enable the proxy (Restore network)
proxy-enable:
	@echo "Enabling RabbitMQ proxy..."
	curl -s -X POST http://localhost:8474/proxies/rabbitmq \
		-H "Content-Type: application/json" \
		-d '{"enabled": true}'
	@echo "\nProxy enabled (Network is UP)."

# 3. Disable the proxy (Break network / Chaos)
proxy-disable:
	@echo "Disabling RabbitMQ proxy..."
	curl -s -X POST http://localhost:8474/proxies/rabbitmq \
		-H "Content-Type: application/json" \
		-d '{"enabled": false}'
	@echo "\nProxy disabled (Network is DOWN)."

# 4. View the status of all proxies (similar to fetch_proxies)
proxy-status:
	@echo "Fetching proxies status..."
	curl -s -X GET http://localhost:8474/proxies | python3 -m json.tool