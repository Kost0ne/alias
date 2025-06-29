# Alias Web Game

This is a simple implementation of the Alias word guessing game using **NiceGUI** and **FastAPI**. Players can create a lobby and invite friends using the generated URL. The application keeps all state in memory.

The host can start timed rounds. During a round only the explainer sees the current word. Other players see a waiting message. Points are awarded for each correct guess and the score for both teams is visible to everyone.

## Requirements

- Python 3.10+
- `nicegui`

Install dependencies and run the server:

```bash
pip install nicegui
python main.py
```

Open the displayed URL in your browser to start creating a lobby.
