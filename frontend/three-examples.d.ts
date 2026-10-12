declare module "three/examples/jsm/loaders/GLTFLoader.js" {
  import type { AnimationClip, Group, LoadingManager } from "three";

  export interface GLTF {
    scene: Group;
    animations: AnimationClip[];
  }

  export class GLTFLoader {
    constructor(manager?: LoadingManager);
    load(
      url: string,
      onLoad: (gltf: GLTF) => void,
      onProgress?: (event: ProgressEvent<EventTarget>) => void,
      onError?: (error: unknown) => void,
    ): void;
  }
}
