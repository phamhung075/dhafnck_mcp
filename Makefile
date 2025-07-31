up:
	docker compose up

test:
	docker compose -f dhafnck_mcp_main/docker/docker-compose.yml -f dhafnck_mcp_main/docker/docker-compose.test.yml up 

e2e-test:
	docker compose -f dhafnck_mcp_main/docker/docker-compose.yml -f dhafnck_mcp_main/docker/docker-compose.test.yml up -d
	docker cp dhafnck_mcp_main/tests/e2e dhafnck-mcp-server:/app/tests/
	docker exec -it dhafnck-mcp-server pytest /app/tests/e2e 