/// <reference types="three" />

declare module 'three' {
  // 为确保不会有类型错误，这里声明缺失的类型
  export const Scene: any;
  export const PerspectiveCamera: any;
  export const WebGLRenderer: any;
  export const AmbientLight: any;
  export const DirectionalLight: any;
  export const HemisphereLight: any;
  export const TextureLoader: any;
  export const SphereGeometry: any;
  export const MeshPhongMaterial: any;
  export const Mesh: any;
  export const BackSide: any;
  export const TorusGeometry: any;
  export const MeshBasicMaterial: any;
  export const Group: any;
  export const MathUtils: any;
  export const Texture: any;
} 