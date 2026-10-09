import type { WorldInputState } from "./worldTypes";

interface PointerOrigin {
  pointerId: number;
  x: number;
  y: number;
  moved: boolean;
}

export class WorldInput {
  private readonly keys = new Set<string>();
  private readonly target: HTMLElement;
  private readonly pointers = new Map<number, { x: number; y: number }>();
  private pointer?: PointerOrigin;
  private pinchDistance: number | null = null;

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
    this.pointers.clear();
  }

  consume(): WorldInputState {
    const left = this.keys.has("a") || this.keys.has("arrowleft");
    const right = this.keys.has("d") || this.keys.has("arrowright");
    const up = this.keys.has("w") || this.keys.has("arrowup");
    const down = this.keys.has("s") || this.keys.has("arrowdown");

    return { moveX: Number(right) - Number(left), moveY: Number(down) - Number(up), zoomDelta: 0 };
  }

  private readonly onKeyDown = (event: KeyboardEvent) => {
    if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", " "].includes(event.key)) event.preventDefault();
    if (event.key.toLowerCase() === "m") {
      event.preventDefault();
      this.target.dispatchEvent(new CustomEvent("world:map-toggle"));
      return;
    }
    this.keys.add(event.key.toLowerCase());
  };

  private readonly onKeyUp = (event: KeyboardEvent) => {
    this.keys.delete(event.key.toLowerCase());
  };

  private readonly onWheel = (event: WheelEvent) => {
    event.preventDefault();
    this.target.dispatchEvent(new CustomEvent("world:zoom", { detail: { delta: event.deltaY > 0 ? -0.08 : 0.08 } }));
  };

  private readonly onPointerDown = (event: PointerEvent) => {
    this.pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
    // Capture every active pointer so both fingers remain tracked during pinch zoom.
    this.target.setPointerCapture(event.pointerId);
    if (this.pointers.size === 1) {
      this.pointer = { pointerId: event.pointerId, x: event.clientX, y: event.clientY, moved: false };
    }
    if (this.pointers.size === 2) this.pinchDistance = this.distanceBetweenPointers();
  };

  private readonly onPointerMove = (event: PointerEvent) => {
    this.pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });

    if (this.pointers.size >= 2) {
      const distance = this.distanceBetweenPointers();
      if (this.pinchDistance && distance > 0) {
        const delta = (distance - this.pinchDistance) / this.pinchDistance;
        if (Math.abs(delta) > 0.005) this.target.dispatchEvent(new CustomEvent("world:zoom", { detail: { delta: Math.max(-0.12, Math.min(0.12, delta)) } }));
      }
      this.pinchDistance = distance;
      return;
    }

    if (!this.pointer) return;
    const dx = event.clientX - this.pointer.x;
    const dy = event.clientY - this.pointer.y;
    if (Math.hypot(dx, dy) > 4) this.pointer.moved = true;
    this.pointer.x = event.clientX;
    this.pointer.y = event.clientY;
    if (this.pointer.moved) this.target.dispatchEvent(new CustomEvent("world:pan", { detail: { dx, dy } }));
  };

  private readonly onPointerUp = (event: PointerEvent) => {
    const wasSingleTap =
      this.pointers.size === 1 &&
      this.pointer !== undefined &&
      this.pointer.pointerId === event.pointerId &&
      !this.pointer.moved;
    if (wasSingleTap) {
      this.target.dispatchEvent(new CustomEvent("world:tap", { detail: { x: event.offsetX, y: event.offsetY } }));
    }
    this.pointers.delete(event.pointerId);
    if (this.pointer?.pointerId === event.pointerId) this.pointer = undefined;
    if (this.pointers.size < 2) this.pinchDistance = null;
  };

  private distanceBetweenPointers(): number {
    const points = [...this.pointers.values()];
    if (points.length < 2) return 0;
    return Math.hypot(points[0].x - points[1].x, points[0].y - points[1].y);
  }
}
