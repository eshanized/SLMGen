# SLMGen UI Roadmap 🚀

This document outlines the planned UI/UX enhancements for SLMGen, focusing on "premium" feel, data visibility, and developer aesthetics.

## Phase 1: Enhanced Core Flows (Immediate) ✅

### 1. ✨ Live Dataset Chat Preview
**Goal**: Instantly validate data and build trust during the Upload step.
- [x] **Client-side JSONL Parsing**: Read the first 5 lines of the uploaded file without sending to server.
- [x] **Chat Bubble Interface**: Render the examples as a conversation (User on right, Assistant on left).
- [x] **Validation Indicators**: Show "✅ Valid Format" or "❌ Missing 'role' key" directly on the bubbles.

### 2. 💻 Training Terminal Simulator
**Goal**: Make the "Generate" step feel powerful and productive.
- [x] **Mock Terminal Component**: A code window that "types out" setup commands in real-time.
- [x] **Commands**: `pip install unsloth`, `loading adapter...`, `optimizing weights...`.
- [x] **Syntax Highlighting**: Green text on black background for that "hacker" aesthetic.

### 3. 🎉 Success Polish
**Goal**: Celebrate the "Notebook Ready" moment.
- [x] **Confetti Explosion**: Trigger confetti when the notebook generation completes.
- [ ] **Sound Effect (Optional)**: A subtle "success" chime (muted by default).

---

## Phase 2: Business & Intelligence (Next Up)

### 4. 💸 Fine-tuning ROI Calculator
**Goal**: Demonstrate the business value of SLMGen vs OpenAI.
- [ ] **Interactive Sliders**: Inputs for "Monthly Tokens", "Average Prompt Length".
- [ ] **Visual Graph**: Bar chart comparing **GPT-4o Cost** vs **SLM Hosting Cost**.
- [ ] **"Savings" Badge**: "You save $X/year!" highlight.

### 5. 📊 Model Comparison Radar
**Goal**: Help users choose the right base model data-drivenly.
- [ ] **Radar Chart**: Compare Llama 3.2 vs Qwen 2.5 vs Phi-3.5.
- [ ] **Axes**: Reasoning, Speed, Context Window, VRAM Usage.

---

## Phase 3: Developer Experience (Future)

### 6. ⌨️ Keyboard Shortcuts
- `Ctrl + Enter` to proceed to next step.
- `Esc` to go back.
- `/` to focus search (if added).

### 7. 🌓 Themes
- **Cyberpunk Mode**: Neon accents.
- **Minimal Mode**: High contrast, no gradients.
