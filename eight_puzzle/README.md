# OCTET — 8 Puzzle AI Solver

An interactive 8-puzzle game with **A* Search** and **BFS** AI solvers.  
Built with **Python (Flask)** + **HTML/CSS/JS**. No external APIs required.

---

## 🚀 How to Run

### 1. Make sure Python 3.8+ is installed
```
python --version
```

### 2. Install Flask
```
pip install flask
```

### 3. Run the server
```
python app.py
```

### 4. Open in browser
**http://localhost:5000**

Share on local network: `http://<your-ip>:5000`

---

## 🎮 Features
- **Manual Play** — click tiles or use arrow keys
- **A* Solver** — with Manhattan or Misplaced Tiles heuristic
- **BFS Solver** — uninformed search (slower, for comparison)
- **Hint System** — shows the optimal next move
- **Step-by-step Playback** — with speed control
- **Custom Puzzle Input** — enter your own starting state
- **AI Stats** — nodes explored, time, optimal path length

## 📁 Structure
```
eight_puzzle/
├── app.py
├── requirements.txt
├── README.md
└── templates/
    └── index.html
```

## 🤖 AI Algorithms Used
- **A* Search** with Manhattan Distance heuristic (optimal + efficient)
- **A* Search** with Misplaced Tiles heuristic
- **BFS** (Breadth-First Search) — uninformed, slower baseline
