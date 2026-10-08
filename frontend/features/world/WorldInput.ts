import type { WorldInputState } from "./worldTypes";

export class WorldInput {
  private readonly keys = new Set<string>();
  private readonly target: HTMLElement;
  private pointer?: { x: number; y: number };

  constructor(target: HTMLElement) {
    this.target = target;
    target.addEventListener("keydown", this.onKeyDown);
    target.addEventListener("keyup", this.onKeyUp);
    target.addEventListener("wheel", this.onWheel, { passive: false });
    target.addEventListener("pointerdown", this.onPointerDown);
    target.addEventListener("pointermove", this.onPointerMove);
    target.addEventListener("pointerup", this.onPointerUp);
    target.addEventListener("pointercancel", this.onPointerUp);
    target.tabIndex = 0;
  }

  destroy(): void {
    this.target.removeEventListener("keydown", this.onKeyDown);
    this.target.removeEventListener("keyup", this.onKeyUp);
    this.target.removeEventListener("wheel", this.onWheel);
    this.target.removeEventListener("pointerdown", this.onPointerDown);
    this.target.removeEventListener("pointermove", this.onPointerMove);
    this.target.removeEventListener("pointerup", this.onPointerUp);
    this.target.removeEventListener("pointercancel", this.onPointerUp);
  }

  consume(): WorldInputState {
    const left = this.keys.has("a") || this.keys.has("arrowleft");
    const right = this.keys.has("d") || this.keys.has("arrowright");
    const up = this.keys.has("w") || this.keys.has("arrowup");
    const down = this.keys.has("s") || this.keys.has("arrowdown");

    return {
      moveX: Number(right) - Number(left),
      moveY: Number(down) - Number(up),
      zoomDelta: 0,
    };
  }

  private readonly onKeyDown = (event: KeyboardEvent) => {
    if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", " "].includes(event.key)) {
      event.preventDefault();
    }
    this.keys.add(event.key.toLowerCase());
  };

  private readonly onKeyUp = (event: KeyboardEvent) => {
    this.keys.delete(event.key.toLowerCase());
  };

  private readonly onWheel = (event: WheelEvent) => {
    event.preventDefault();
    const direction = event.deltaY > 0 ? -1 : 1;
    this.target.dispatchEvent(
      new CustomEvent("world:zoom", { detail: { delta: direction * 0.08 } }),
    );
  };

  private readonly onPointerDown = (event: PointerEvent) => {
    this.pointer = { x: event.clientX, y: event.clientY };
    this.target.setPointerCapture(event.pointerId);
  };

  private readonly onPointerMove = (event: PointerEvent) => {
    if (!this.pointer) return;
    const dx = event.clientX - this.pointer.x;
    const dy = event.clientY - this.pointer.y;
    this.pointer = { x: event.clientX, y: event.clientY };
    this.target.dispatchEvent(new CustomEvent("world:pan", { detail: { dx, dy } }));
  };

  private readonly onPointerUp = () => {
    this.pointer = undefined;
  };
}
