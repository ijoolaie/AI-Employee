declare module "three/examples/jsm/loaders/GLTFLoader.js" {
  import { Group, Loader } from "three";

  export interface GLTF {
    scene: Group;
  }

  export class GLTFLoader extends Loader {
    loadAsync(url: string): Promise<GLTF>;
  }
}
