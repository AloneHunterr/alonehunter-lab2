# AloneHunter FramePack Lab

Isolated experimental namespace for the FramePack/Kaggle long-form video-generation route.

## Safety boundary
- Do not modify existing Wan, VK, publishing, or production routes.
- Keep credentials out of the repository; use runtime secrets/environment variables.
- Do not commit model weights or generated video artifacts.
- Require reproducible physical benchmark evidence before production handoff.

## Target
Validate a repeatable premium-class long-form video generation pipeline capable of producing meaningful continuous scene material rather than relying on 1–2 five-second generations per day.

## Initial gate
1. Prove Kaggle runtime/GPU compatibility.
2. Prove FramePack inference from controlled source image and prompt.
3. Measure runtime, VRAM, output metadata, failures, and usable duration.
4. Connect the proven output to existing Drive transport and Visual QA only after PASS.
