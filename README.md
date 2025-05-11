# Monadic

## Prerequisites

### On macOS

```bash
brew update
brew install python direnv
```

### On Linux
```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip direnv
```

## Shell Setup

Ensure your shell loads direnv correctly.

### bash
```bash
eval "$(direnv hook bash)"
```

### zsh
```bash
eval "$(direnv hook zsh)"
```

### fish
```bash
eval (direnv hook fish)
```

Then restart your shell our source the config file

## Project Setup

1. Clone the repo
```bash
git clone https://github.com/yourusername/monadic.git
cd monadic
```

2. Create .venv/
```bash
python3 -m venv .venv
```

3. Recommended .envrc
```bash
layout python3

# (Optional) expose your project root on PYTHONPATH so imports always work
export PYTHONPATH=$(pwd)

# Load any environment variables you've defined in .env
dotenv
```

4. Recommended .env
```dotenv
# ensure this file is in .gitignore!
OPENAI_API_KEY=your-api-key-here

# include any other desired environment variables below
```

4. Allow direnv
```bash
direnv allow
```
You should now see your shell environment automatically activate .venv.

5. Upgrade pip and install dependencies to venv
```bash
pip install --upgrade pip
pip install -r requirements.txt

# Optional install for pytest unit testing
pip install -r requirements-dev.txt
```

Optional: if you’re using pip-tools, compile requirements.txt from requirements.in:
```bash
pip-compile requirements.in
```

---

Example directory structure:
```
monadic/
├── .venv/                 # virtualenv (git-ignored)
├── .envrc                 # direnv environment hook (git-ignored)
├── requirements.txt       # Python dependencies
├── monadic/               # main package
├── tests/                 # mirrored test structure
└── README.md              # this guide!
```

---

## You're Ready to Run!

Try:
```bash
python client.py
```

### client.py

This script launches a voice-enabled or text-based interactive session with a conversation agent (Interact).

### How To Use

By default $\texttt{client.py}$  loads directly into a query. Start typing and press $\texttt{enter}$ to send query.

If query line is left blank and the $\texttt{enter}$ key is pressed, transcription mode will be activated. Do be aware this uses OpenAI API transcription and there is no guard on recording time limit. The only way to exit out of this without sending the audio is to forcefully close $\texttt{client.py}$.

#### Input Commands

Toggle logging output to terminal: (By default this is toggled off)
```
audit
```

Reset the conversaton instance and clear the terminal screen:

```
clear
```

Exit client.py and return to terminal:
```
exit
```


## Testing

or test coverage with:
```bash
pytest --cov=monadic
```
