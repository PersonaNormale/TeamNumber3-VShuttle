.PHONY: run install-backend install-frontend

run:
	./run_fullstack.sh

install-backend:
	cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

install-frontend:
	cd frontend && npm install
