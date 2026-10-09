import { afterEach, describe, expect, it } from "vitest";
import { WorldInput } from "../features/world/WorldInput";

class PointerInputEvent extends Event {
  constructor(
    type: string,
    readonly pointerId: number,
    readonly clientX: number,
    readonly clientY: number,
    readonly offsetX: number,
    readonly offsetY: number,
  ) {
    super(type);
  }
}

class InputTarget extends EventTarget {
  tabIndex = -1;
  capturedPointers: number[] = [];
  ownerDocument = { defaultView: new EventTarget() };

  setPointerCapture(pointerId: number) {
    this.capturedPointers.push(pointerId);
  }
}

describe("WorldInput pointer lifecycle", () => {
  let input: WorldInput | undefined;

  afterEach(() => {
    input?.destroy();
    input = undefined;
  });

  it("captures both pointers and does not emit a tap when a pinch ends", () => {
    const target = new InputTarget();
    const taps: Array<{ x: number; y: number }> = [];
    target.addEventListener("world:tap", (event) => {
      taps.push((event as CustomEvent<{ x: number; y: number }>).detail);
    });
    input = new WorldInput(target as unknown as HTMLElement);

    target.dispatchEvent(new PointerInputEvent("pointerdown", 1, 10, 10, 10, 10));
    target.dispatchEvent(new PointerInputEvent("pointerdown", 2, 30, 10, 30, 10));
    target.dispatchEvent(new PointerInputEvent("pointerup", 1, 10, 10, 10, 10));
    target.dispatchEvent(new PointerInputEvent("pointerup", 2, 30, 10, 30, 10));

    expect(target.capturedPointers).toEqual([1, 2]);
    expect(taps).toEqual([]);
  });

  it("still emits a tap for a single pointer", () => {
    const target = new InputTarget();
    const taps: Array<{ x: number; y: number }> = [];
    target.addEventListener("world:tap", (event) => {
      taps.push((event as CustomEvent<{ x: number; y: number }>).detail);
    });
    input = new WorldInput(target as unknown as HTMLElement);

    target.dispatchEvent(new PointerInputEvent("pointerdown", 7, 14, 22, 14, 22));
    target.dispatchEvent(new PointerInputEvent("pointerup", 7, 14, 22, 14, 22));

    expect(taps).toEqual([{ x: 14, y: 22 }]);
  });

  it("does not emit a tap when a pointer gesture is cancelled", () => {
    const target = new InputTarget();
    const taps: Array<{ x: number; y: number }> = [];
    target.addEventListener("world:tap", (event) => {
      taps.push((event as CustomEvent<{ x: number; y: number }>).detail);
    });
    input = new WorldInput(target as unknown as HTMLElement);

    target.dispatchEvent(new PointerInputEvent("pointerdown", 3, 14, 22, 14, 22));
    target.dispatchEvent(new PointerInputEvent("pointercancel", 3, 14, 22, 14, 22));

    expect(taps).toEqual([]);
  });

  it("does not emit a tap if the second pinch pointer is cancelled", () => {
    const target = new InputTarget();
    const taps: Array<{ x: number; y: number }> = [];
    target.addEventListener("world:tap", (event) => {
      taps.push((event as CustomEvent<{ x: number; y: number }>).detail);
    });
    input = new WorldInput(target as unknown as HTMLElement);

    target.dispatchEvent(new PointerInputEvent("pointerdown", 11, 10, 10, 10, 10));
    target.dispatchEvent(new PointerInputEvent("pointerdown", 12, 30, 10, 30, 10));
    target.dispatchEvent(new PointerInputEvent("pointercancel", 12, 30, 10, 30, 10));
    target.dispatchEvent(new PointerInputEvent("pointerup", 11, 10, 10, 10, 10));

    expect(taps).toEqual([]);
  });

  it("clears held movement keys when the browser window loses focus", () => {
    const target = new InputTarget();
    input = new WorldInput(target as unknown as HTMLElement);

    const keydown = new Event("keydown");
    Object.defineProperty(keydown, "key", { value: "w" });
    target.dispatchEvent(keydown);
    expect(input.consume().moveY).toBe(-1);

    (target.ownerDocument.defaultView as EventTarget).dispatchEvent(new Event("blur"));

    expect(input.consume()).toEqual({ moveX: 0, moveY: 0, zoomDelta: 0 });
  });

});
