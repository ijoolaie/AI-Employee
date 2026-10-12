"use client";

import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { WorldInput } from "./WorldInput";
import { screenPanToWorldDelta } from "./WorldPan";
import type { WorldEmployee } from "./WorldState";
import { isRoomSceneAccessUsable } from "./WorldRoomSceneAccess";
import type { RoomFurniturePlacement, WorldRoomSceneConfig } from "./WorldRoomSceneConfig";

type WorkerVisual = {
  id: string;
  group: any;
  hit: any;
  ring: any;
  status: any;
  state: string;
};

const STATE_COLOR: Record<WorldEmployee["state"], number> = {
  WORKING: 0x28b887,
  WAITING_APPROVAL: 0xf2b84b,
  IDLE: 0x9aa8bb,
  BLOCKED: 0xef6a6a,
  ESCALATED: 0xf28c45,
  COMPLETED: 0x8a83ef,
};

const DEPARTMENTS = [
  { name: "COMMAND", x: -11, z: -7, color: 0xe8e1d4, accent: 0x8172d8 },
  { name: "SALES", x: 0, z: -7, color: 0xe6eadf, accent: 0x55a88d },
  { name: "CUSTOMER CARE", x: 11, z: -7, color: 0xf0e3d8, accent: 0xe89a67 },
  { name: "OPERATIONS", x: -7, z: 6, color: 0xe1e8ee, accent: 0x6197c5 },
  { name: "ENGINEERING", x: 6, z: 6, color: 0xe9e2f0, accent: 0x9c78c7 },
];

type SurfaceTexture = "wood" | "fabric" | "plaster" | "stone";
const surfaceTextureCache = new Map<SurfaceTexture, THREE.CanvasTexture>();

/**
 * Small seamless canvas textures add actual surface detail without shipping large
 * image files. They are deliberately subtle: texture should enrich the authored
 * palette, not look like a noisy filter at the isometric camera distance.
 */
function getSurfaceTexture(kind: SurfaceTexture): THREE.CanvasTexture {
  const cached = surfaceTextureCache.get(kind);
  if (cached) return cached;

  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 256;
  const context = canvas.getContext("2d");
  if (!context) throw new Error("Canvas 2D is required to create World surface textures");

  const base = kind === "wood" ? "#b98558" : kind === "fabric" ? "#8799a6" : kind === "stone" ? "#b9b7ae" : "#e8e4db";
  context.fillStyle = base;
  context.fillRect(0, 0, canvas.width, canvas.height);

  // Fixed-seed pseudo-random noise keeps each material stable between renders.
  let seed = kind.length * 7919;
  const random = () => {
    seed = (seed * 1664525 + 1013904223) >>> 0;
    return seed / 4294967296;
  };

  if (kind === "wood") {
    for (let row = 0; row < 34; row += 1) {
      const y = row * 8 + random() * 4;
      context.strokeStyle = row % 3 === 0 ? "rgba(79,45,25,.20)" : "rgba(244,204,154,.22)";
      context.lineWidth = row % 5 === 0 ? 2 : 1;
      context.beginPath();
      context.moveTo(0, y);
      for (let x = 0; x <= 256; x += 16) {
        context.lineTo(x, y + Math.sin(x * 0.035 + row) * (1 + random() * 2));
      }
      context.stroke();
    }
    for (let knot = 0; knot < 5; knot += 1) {
      const x = 20 + random() * 216;
      const y = 20 + random() * 216;
      context.strokeStyle = "rgba(85,48,27,.17)";
      context.beginPath();
      context.ellipse(x, y, 5 + random() * 8, 2 + random() * 4, 0, 0, Math.PI * 2);
      context.stroke();
    }
  } else if (kind === "fabric") {
    for (let offset = 0; offset < 256; offset += 4) {
      context.strokeStyle = offset % 8 === 0 ? "rgba(255,255,255,.13)" : "rgba(27,43,57,.08)";
      context.lineWidth = 1;
      context.beginPath(); context.moveTo(offset, 0); context.lineTo(offset, 256); context.stroke();
      context.beginPath(); context.moveTo(0, offset); context.lineTo(256, offset); context.stroke();
    }
  } else {
    for (let i = 0; i < 1500; i += 1) {
      const shade = random() > 0.5 ? 255 : 35;
      const alpha = kind === "stone" ? 0.035 : 0.025;
      context.fillStyle = `rgba(${shade},${shade},${shade},${alpha})`;
      const size = kind === "stone" ? 1 + random() * 5 : 1 + random() * 2;
      context.fillRect(random() * 256, random() * 256, size, size);
    }
    if (kind === "stone") {
      for (let y = 24; y < 256; y += 48) {
        context.strokeStyle = "rgba(80,80,74,.12)";
        context.lineWidth = 1;
        context.beginPath(); context.moveTo(0, y); context.lineTo(256, y + random() * 8); context.stroke();
      }
    }
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.RepeatWrapping;
  texture.generateMipmaps = true;
  texture.minFilter = THREE.LinearMipmapLinearFilter;
  texture.magFilter = THREE.LinearFilter;
  texture.repeat.set(kind === "wood" ? 1.8 : 1, kind === "wood" ? 1 : 1);
  surfaceTextureCache.set(kind, texture);
  return texture;
}


function box(
  parent: any,
  size: [number, number, number],
  position: [number, number, number],
  color: number,
  options: { roughness?: number; metalness?: number; emissive?: number; emissiveIntensity?: number; castShadow?: boolean; receiveShadow?: boolean; texture?: SurfaceTexture } = {},
) {
  const mesh = new THREE.Mesh(
    new THREE.BoxGeometry(...size),
    new THREE.MeshStandardMaterial({ color, map: options.texture ? getSurfaceTexture(options.texture) : undefined, roughness: options.roughness ?? 0.78, metalness: options.metalness ?? 0, emissive: options.emissive ?? 0, emissiveIntensity: options.emissiveIntensity ?? 0 }),
  );
  mesh.position.set(...position);
  mesh.castShadow = options.castShadow ?? true;
  mesh.receiveShadow = options.receiveShadow ?? true;
  parent.add(mesh);
  return mesh;
}

function cylinder(parent: any, radiusTop: number, radiusBottom: number, height: number, position: [number, number, number], color: number, segments = 12) {
  const mesh = new THREE.Mesh(
    new THREE.CylinderGeometry(radiusTop, radiusBottom, height, segments),
    new THREE.MeshStandardMaterial({ color, roughness: 0.84 }),
  );
  mesh.position.set(...position);
  mesh.castShadow = true;
  parent.add(mesh);
  return mesh;
}

function sphere(parent: any, radius: number, position: [number, number, number], color: number, scale: [number, number, number] = [1, 1, 1]) {
  const mesh = new THREE.Mesh(
    new THREE.SphereGeometry(radius, 16, 12),
    new THREE.MeshStandardMaterial({ color, roughness: 0.8 }),
  );
  mesh.position.set(...position);
  mesh.scale.set(...scale);
  mesh.castShadow = true;
  parent.add(mesh);
  return mesh;
}

function makeLabel(text: string, color: string) {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 128;
  const ctx = canvas.getContext("2d");
  if (!ctx) return null;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "rgba(24, 35, 48, .88)";
  ctx.beginPath();
  ctx.roundRect(12, 12, 488, 104, 28);
  ctx.fill();
  ctx.fillStyle = color;
  ctx.font = "bold 34px system-ui, sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(text, 256, 64);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  const material = new THREE.SpriteMaterial({ map: texture, transparent: true, depthWrite: false });
  const sprite = new THREE.Sprite(material);
  sprite.scale.set(5.5, 1.38, 1);
  return sprite;
}

function addDesk(parent: any, x: number, z: number, accent: number) {
  const desk = new THREE.Group();
  desk.position.set(x, 0, z);
  parent.add(desk);
  box(desk, [3.15, 0.18, 1.65], [0, 1.32, 0], 0xffffff, { texture: "wood", roughness: 0.68 });
  for (const dx of [-1.35, 1.35]) {
    for (const dz of [-0.62, 0.62]) box(desk, [0.12, 1.28, 0.12], [dx, 0.64, dz], 0x806044);
  }
  // Monitor housing, illuminated display, stand and foot read as a complete workstation.
  box(desk, [1.18, 0.86, 0.12], [0, 1.92, -0.46], 0x34465a);
  box(desk, [1.03, 0.68, 0.035], [0, 1.93, -0.385], 0x20354a, { roughness: 0.42 });
  box(desk, [0.88, 0.53, 0.018], [0, 1.96, -0.362], accent, { emissive: accent, emissiveIntensity: 0.22, roughness: 0.4 });
  box(desk, [0.12, 0.22, 0.12], [0, 1.47, -0.43], 0x526273);
  box(desk, [0.5, 0.055, 0.24], [0, 1.39, -0.34], 0x526273);
  // Keyboard, mouse and a small stack of notes break up the empty desk surface.
  box(desk, [0.94, 0.045, 0.28], [0, 1.45, 0.24], 0x354150);
  for (let key = 0; key < 9; key += 1) {
    box(desk, [0.065, 0.012, 0.035], [-0.36 + key * 0.09, 1.478, 0.19], 0xaebbc5);
  }
  box(desk, [0.28, 0.035, 0.22], [0.82, 1.43, 0.22], 0xeee7d9);
  box(desk, [0.28, 0.035, 0.22], [0.82, 1.46, 0.22], 0xfaf6ed);
  const mouse = sphere(desk, 0.105, [0.62, 1.49, 0.27], 0xd8e0e5, [0.72, 0.55, 1.1]);
  mouse.castShadow = true;
  box(desk, [0.48, 0.035, 0.34], [-1.03, 1.43, 0.28], 0x6b8caa);
  box(desk, [0.42, 0.025, 0.29], [-1.03, 1.46, 0.28], 0xf0e4c9);
  const mug = cylinder(desk, 0.12, 0.12, 0.22, [1.08, 1.51, 0.35], 0xf7f0df, 12);
  mug.castShadow = true;
  const chair = new THREE.Group();
  chair.position.set(0, 0, 1.35);
  desk.add(chair);
  cylinder(chair, 0.5, 0.52, 0.16, [0, 0.72, 0], 0x526c80, 16);
  box(chair, [0.92, 0.95, 0.16], [0, 1.2, 0.42], 0x8799a6, { texture: "fabric", roughness: 0.96 });
  cylinder(chair, 0.12, 0.15, 0.58, [0, 0.36, 0], 0x48596a, 10);
  return desk;
}

function addWorker(parent: any, employee: WorldEmployee): WorkerVisual {
  // Build a warm, toy-like 3D character with an individually varied face, hairstyle and work outfit.
  const group = new THREE.Group();
  group.userData.employeeId = employee.id;
  parent.add(group);

  const outfitPalette = [0x557ca5, 0x6b9b82, 0xc78360, 0x8b78b6, 0x4e9aab, 0xc28b4c];
  const skinPalette = [0xf0c8a5, 0xdca47e, 0xb97855, 0xf3d8bd, 0x8f5d45, 0xe8b594];
  const hairPalette = [0x51413b, 0x302c2b, 0x7b5034, 0x9b744a, 0x454b55, 0x6b3731];
  const seed = Math.abs(hash(employee.id));
  const color = outfitPalette[seed % outfitPalette.length];
  const skin = skinPalette[Math.floor(seed / 7) % skinPalette.length];
  const hair = hairPalette[Math.floor(seed / 13) % hairPalette.length];
  const hairstyle = Math.floor(seed / 19) % 4;

  // Rounded torso, shoulders and a contrasting collar make the silhouette read as a character, not a token.
  cylinder(group, 0.34, 0.42, 0.78, [0, 1.0, 0.02], color, 18);
  sphere(group, 0.22, [-0.27, 1.25, 0.02], color, [1.1, 0.82, 1]);
  sphere(group, 0.22, [0.27, 1.25, 0.02], color, [1.1, 0.82, 1]);
  cylinder(group, 0.13, 0.15, 0.2, [0, 1.39, -0.01], skin, 12);
  // Shirt collar, tie/scarf and a small employee badge add readable workwear detail.
  box(group, [0.16, 0.12, 0.09], [-0.095, 1.34, 0.31], 0xf5eee2);
  box(group, [0.16, 0.12, 0.09], [0.095, 1.34, 0.31], 0xf5eee2);
  box(group, [0.075, 0.24, 0.045], [0, 1.22, 0.365], seed % 2 ? 0xe9c46a : 0xd7e7f0);
  box(group, [0.12, 0.14, 0.035], [0.23, 1.08, 0.345], 0xf4eee1);
  box(group, [0.055, 0.055, 0.025], [0.23, 1.08, 0.368], 0x4f9b87);

  // Head and ears use a wider, softly rounded silhouette.
  sphere(group, 0.35, [0, 1.68, -0.02], skin, [1.02, 1.04, 0.98]);
  sphere(group, 0.075, [-0.335, 1.65, -0.015], skin, [0.78, 1, 0.82]);
  sphere(group, 0.075, [0.335, 1.65, -0.015], skin, [0.78, 1, 0.82]);

  // Four deterministic hairstyles vary the cast while remaining inexpensive procedural geometry.
  sphere(group, 0.37, [0, 1.86, -0.085], hair, [1.02, 0.52, 0.98]);
  if (hairstyle === 0) {
    sphere(group, 0.19, [0, 1.79, 0.235], hair, [1.25, 0.48, 0.45]);
    sphere(group, 0.12, [-0.25, 1.78, 0.12], hair, [0.85, 0.95, 0.72]);
  } else if (hairstyle === 1) {
    sphere(group, 0.2, [-0.12, 1.91, 0.15], hair, [1.05, 0.68, 0.62]);
    sphere(group, 0.17, [0.18, 1.91, 0.13], hair, [1.0, 0.6, 0.6]);
  } else if (hairstyle === 2) {
    sphere(group, 0.12, [-0.29, 1.7, 0.04], hair, [0.75, 1.15, 0.7]);
    sphere(group, 0.12, [0.29, 1.7, 0.04], hair, [0.75, 1.15, 0.7]);
    sphere(group, 0.16, [0.02, 1.96, -0.02], hair, [1.0, 0.52, 0.9]);
  } else {
    sphere(group, 0.16, [0.12, 1.96, 0.12], hair, [1.05, 0.55, 0.8]);
    sphere(group, 0.12, [-0.22, 1.86, 0.16], hair, [0.8, 0.75, 0.6]);
  }

  // Layered eyes with tiny catchlights read more clearly at an isometric camera distance.
  const irisPalette = [0x4d786e, 0x4a617f, 0x765342, 0x596b87];
  const iris = irisPalette[Math.floor(seed / 23) % irisPalette.length];
  for (const side of [-1, 1]) {
    sphere(group, 0.073, [side * 0.12, 1.69, 0.292], 0xfffbf3, [1, 1.05, 0.5]);
    sphere(group, 0.041, [side * 0.115, 1.685, 0.326], iris, [0.95, 1.1, 0.5]);
    sphere(group, 0.022, [side * 0.115, 1.686, 0.345], 0x202a32, [0.9, 1.05, 0.5]);
    sphere(group, 0.012, [side * 0.128, 1.704, 0.354], 0xffffff, [1, 1, 0.5]);
    box(group, [0.14, 0.028, 0.035], [side * 0.12, 1.79, 0.285], hair);
  }
  sphere(group, 0.048, [0, 1.61, 0.325], skin, [0.78, 0.82, 1.1]);
  const smile = new THREE.Mesh(
    new THREE.TorusGeometry(0.073, 0.012, 6, 18, Math.PI),
    new THREE.MeshStandardMaterial({ color: 0x9a5c51, roughness: 0.9 }),
  );
  // Flip the half-ring so its ends rise gently into a friendly smile.
  smile.rotation.z = Math.PI;
  smile.scale.set(1.2, 0.72, 1);
  smile.position.set(0, 1.56, 0.326);
  group.add(smile);
  // Subtle cheeks make the style friendly without turning the employees into oversized mascots.
  sphere(group, 0.045, [-0.22, 1.61, 0.275], 0xe99b8b, [1, 0.65, 0.4]);
  sphere(group, 0.045, [0.22, 1.61, 0.275], 0xe99b8b, [1, 0.65, 0.4]);

  // Bent legs and shoes create a compact seated silhouette beneath the desk.
  cylinder(group, 0.14, 0.15, 0.42, [-0.2, 0.48, 0.05], 0x33445b, 12).rotation.x = Math.PI / 2;
  cylinder(group, 0.14, 0.15, 0.42, [0.2, 0.48, 0.05], 0x33445b, 12).rotation.x = Math.PI / 2;
  box(group, [0.25, 0.13, 0.34], [-0.2, 0.2, 0.3], 0x293545);
  box(group, [0.25, 0.13, 0.34], [0.2, 0.2, 0.3], 0x293545);

  // Sleeves and skin-toned forearms angle toward the keyboard.
  const leftSleeve = cylinder(group, 0.12, 0.15, 0.34, [-0.29, 1.29, 0.15], color, 12);
  leftSleeve.rotation.x = 0.72;
  leftSleeve.rotation.z = -0.24;
  const rightSleeve = cylinder(group, 0.12, 0.15, 0.34, [0.29, 1.29, 0.15], color, 12);
  rightSleeve.rotation.x = 0.72;
  rightSleeve.rotation.z = 0.24;
  const leftArm = cylinder(group, 0.075, 0.09, 0.3, [-0.31, 1.4, 0.48], skin, 12);
  leftArm.rotation.x = 0.72;
  leftArm.rotation.z = -0.18;
  const rightArm = cylinder(group, 0.075, 0.09, 0.3, [0.31, 1.4, 0.48], skin, 12);
  rightArm.rotation.x = 0.72;
  rightArm.rotation.z = 0.18;
  sphere(group, 0.09, [-0.31, 1.46, 0.77], skin, [1, 0.7, 1.1]);
  sphere(group, 0.09, [0.31, 1.46, 0.77], skin, [1, 0.7, 1.1]);
  // Keep the forearms in a small reusable rig so working employees have life
  // beyond a pulsing status light, without moving their assigned desk anchors.
  group.userData.workRig = {
    leftSleeve,
    rightSleeve,
    leftArm,
    rightArm,
    baseLeftSleeveX: leftSleeve.rotation.x,
    baseRightSleeveX: rightSleeve.rotation.x,
    baseLeftArmX: leftArm.rotation.x,
    baseRightArmX: rightArm.rotation.x,
    phase: (Math.abs(hash(employee.id)) % 100) / 100 * Math.PI * 2,
  };

  const ring = new THREE.Mesh(
    new THREE.TorusGeometry(0.82, 0.05, 8, 32),
    new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.92 }),
  );
  ring.rotation.x = -Math.PI / 2;
  ring.position.y = 0.07;
  group.add(ring);

  const statusColor = STATE_COLOR[employee.state];
  const status = new THREE.Mesh(
    new THREE.SphereGeometry(0.14, 12, 10),
    new THREE.MeshStandardMaterial({ color: statusColor, emissive: statusColor, emissiveIntensity: 0.32 }),
  );
  status.position.set(0.42, 2.2, 0);
  group.add(status);

  const hit = new THREE.Mesh(
    new THREE.SphereGeometry(1.05, 12, 10),
    new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false }),
  );
  hit.position.y = 1.0;
  hit.userData.employeeId = employee.id;
  group.add(hit);

  const label = makeLabel(employee.name.slice(0, 24), "#f7fafc");
  if (label) {
    label.position.set(0, 2.72, 0);
    label.scale.set(3.5, 0.86, 1);
    group.add(label);
  }
  group.userData.state = employee.state;
  return { id: employee.id, group, hit, ring, status, state: employee.state };
}

function addCEOAvatar(scene: any) {
  const avatar = new THREE.Group();
  avatar.name = "player-ceo-avatar";

  const material = (color: number, roughness = 0.76, metalness = 0) =>
    new THREE.MeshStandardMaterial({ color, roughness, metalness });
  const suit = material(0x243c55, 0.72);
  const suitLight = material(0x315b72, 0.74);
  const skin = material(0xe7b995, 0.84);
  const hair = material(0x342b2a, 0.9);
  const shirt = material(0xf4f0e7, 0.72);
  const tie = material(0xd6a64f, 0.62);
  const shoe = material(0x1a2633, 0.66);
  const eye = material(0x25313a, 0.8);
  const accent = material(0x62d5c2, 0.45, 0.08);

  const addMesh = (geometry: THREE.BufferGeometry, mat: THREE.Material, position: [number, number, number], parent: THREE.Object3D = avatar) => {
    const mesh = new THREE.Mesh(geometry, mat);
    mesh.position.set(...position);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    parent.add(mesh);
    return mesh;
  };
  const addSphere = (radius: number, position: [number, number, number], mat: THREE.Material, scale: [number, number, number] = [1, 1, 1]) => {
    const mesh = addMesh(new THREE.SphereGeometry(radius, 20, 14), mat, position);
    mesh.scale.set(...scale);
    return mesh;
  };

  // Tailored silhouette: neck, fitted jacket, shirt insert, lapels and a restrained tie.
  addMesh(new THREE.CylinderGeometry(0.12, 0.14, 0.2, 16), skin, [0, 1.43, 0]);
  const body = addMesh(new THREE.CapsuleGeometry(0.39, 0.6, 5, 12), suit, [0, 0.99, 0]);
  body.name = "ceo-tailored-jacket";
  addMesh(new THREE.CapsuleGeometry(0.205, 0.42, 3, 10), shirt, [0, 1.12, 0.265]);
  addMesh(new THREE.CylinderGeometry(0.045, 0.075, 0.34, 5), tie, [0, 1.12, 0.34]);
  // Angular lapels give the torso a tailored, intentional silhouette at game camera distance.
  const lapelGeometry = new THREE.BufferGeometry();
  lapelGeometry.setAttribute("position", new THREE.Float32BufferAttribute([
    0, 1.36, 0.36, -0.19, 1.28, 0.29, -0.055, 1.02, 0.39,
    0, 1.36, 0.36, 0.19, 1.28, 0.29, 0.055, 1.02, 0.39,
  ], 3));
  lapelGeometry.computeVertexNormals();
  addMesh(lapelGeometry, suitLight, [0, 0, 0]);
  addMesh(new THREE.BoxGeometry(0.16, 0.07, 0.035), accent, [-0.24, 1.06, 0.31]);
  addMesh(new THREE.BoxGeometry(0.11, 0.045, 0.035), tie, [0.21, 0.94, 0.34]);

  // Face, ears and layered hair read as a designed character rather than a generic capsule.
  addSphere(0.29, [0, 1.72, 0.02], skin, [0.98, 1.08, 0.94]);
  addSphere(0.075, [-0.285, 1.69, 0.02], skin, [0.72, 1, 0.8]);
  addSphere(0.075, [0.285, 1.69, 0.02], skin, [0.72, 1, 0.8]);
  addSphere(0.30, [0, 1.91, -0.055], hair, [1.02, 0.58, 0.96]);
  addSphere(0.19, [-0.13, 1.94, 0.13], hair, [1.05, 0.62, 0.72]);
  addSphere(0.15, [0.08, 1.98, 0.12], hair, [1.05, 0.56, 0.72]);
  addSphere(0.095, [0.24, 1.86, 0.04], hair, [0.72, 1.0, 0.8]);

  // Eyes, brows, nose and smile remain legible without overloading the low-poly style.
  for (const side of [-1, 1]) {
    addSphere(0.058, [side * 0.105, 1.735, 0.282], shirt, [1, 1.05, 0.5]);
    addSphere(0.029, [side * 0.105, 1.733, 0.309], eye, [1, 1, 0.55]);
    addSphere(0.011, [side * 0.115, 1.747, 0.319], shirt, [1, 1, 0.5]);
    const brow = addMesh(new THREE.BoxGeometry(0.13, 0.026, 0.035), hair, [side * 0.105, 1.815, 0.277]);
    brow.rotation.z = side * -0.08;
  }
  addSphere(0.043, [0, 1.675, 0.302], skin, [0.82, 0.86, 1]);
  const smile = addMesh(new THREE.TorusGeometry(0.06, 0.01, 6, 18, Math.PI), material(0x985e50, 0.92), [0, 1.625, 0.291]);
  smile.rotation.z = Math.PI;
  smile.scale.set(1.1, 0.72, 1);

  // Articulated legs with tailored trousers and shoes.
  const limbMaterial = material(0x26384a, 0.78);
  const leftLeg = new THREE.Group();
  leftLeg.position.set(-0.15, 0.52, 0);
  avatar.add(leftLeg);
  addMesh(new THREE.CapsuleGeometry(0.105, 0.25, 3, 9), limbMaterial, [0, -0.13, 0], leftLeg);
  addMesh(new THREE.BoxGeometry(0.22, 0.12, 0.34), shoe, [0, -0.29, 0.105], leftLeg);
  const rightLeg = leftLeg.clone();
  rightLeg.position.x = 0.15;
  avatar.add(rightLeg);

  // Shoulder joints keep the arms attached while the walk cycle swings them.
  const leftArm = new THREE.Group();
  leftArm.position.set(-0.36, 1.25, 0);
  avatar.add(leftArm);
  addMesh(new THREE.CapsuleGeometry(0.105, 0.27, 3, 9), suitLight, [0, -0.17, 0.015], leftArm);
  addMesh(new THREE.SphereGeometry(0.072, 12, 10), skin, [0, -0.36, 0.055], leftArm);
  const rightArm = leftArm.clone();
  rightArm.position.x = 0.36;
  avatar.add(rightArm);

  avatar.userData.walkRig = { leftLeg, rightLeg, leftArm, rightArm };
  avatar.userData.walkPhase = 0;
  avatar.userData.body = body;
  avatar.userData.artStyle = "stylized-executive-v2";

  const marker = new THREE.Mesh(
    new THREE.TorusGeometry(0.58, 0.045, 8, 28),
    new THREE.MeshBasicMaterial({ color: 0x5eead4, transparent: true, opacity: 0.9 }),
  );
  marker.rotation.x = -Math.PI / 2;
  marker.position.y = 0.07;
  avatar.add(marker);

  // Spawn just beyond the lobby coffee-table footprint so collision never traps the player at startup.
  avatar.position.set(0, 0, 4.4);
  scene.add(avatar);
  return avatar;
}

function addLockedRoom(scene: any) {
  const room = new THREE.Group();
  room.name = "room-entrance";
  // Keep the room physically closed until a current, unexpired server authorization exists.
  box(room, [3.05, 3.5, 0.28], [-2.575, 1.75, 0], 0x38495a);
  box(room, [3.05, 3.5, 0.28], [2.575, 1.75, 0], 0x38495a);
  box(room, [2.1, 0.75, 0.28], [0, 3.125, 0], 0x38495a);
  const doorway = box(room, [2.1, 2.75, 0.08], [0, 1.38, 0.17], 0x1b2938);
  const door = box(room, [1.65, 2.35, 0.1], [0, 1.25, 0.31], 0x526c80, { metalness: 0.15 });
  sphere(room, 0.07, [0.58, 1.22, 0.39], 0xf5cf77);
  box(room, [2.4, 0.14, 0.22], [0, 2.9, 0.34], 0xf5cf77, { emissive: 0x7a5b22, emissiveIntensity: 0.2 });
  const lockedLabel = makeLabel("LOCKED ROOM  •  E TO INSPECT", "#f5d9a4");
  if (lockedLabel) { lockedLabel.position.set(0, 4.05, 0.2); lockedLabel.scale.set(5.2, 1.1, 1); room.add(lockedLabel); }
  const activeLabel = makeLabel("AUTHORIZED ROOM", "#baf4d8");
  if (activeLabel) { activeLabel.position.set(0, 4.05, 0.2); activeLabel.scale.set(5.2, 1.1, 1); activeLabel.visible = false; room.add(activeLabel); }
  room.userData.door = door;
  room.userData.doorway = doorway;
  room.userData.lockedLabel = lockedLabel;
  room.userData.activeLabel = activeLabel;
  room.position.set(0, 0, 12.4);
  scene.add(room);
  return room;
}

function addAuthorizedRoomInterior(scene: any) {
  const interior = new THREE.Group();
  interior.name = "authorized-room-interior";
  interior.visible = false;
  box(interior, [8, 0.16, 8.2], [0, 0.08, 17.1], 0xdce7df);
  box(interior, [8, 3.5, 0.2], [0, 1.75, 21.2], 0x536575);
  box(interior, [0.2, 3.5, 8.2], [-4, 1.75, 17.1], 0x536575);
  box(interior, [0.2, 3.5, 8.2], [4, 1.75, 17.1], 0x536575);
  const furnitureGroup = new THREE.Group();
  furnitureGroup.name = "room-configured-furniture";
  interior.add(furnitureGroup);
  const label = makeLabel("AUTHORIZED ROOM INSTANCE", "#f5d9a4");
  if (label) { label.position.set(0, 3.3, 19.8); label.scale.set(4.6, 0.9, 1); interior.add(label); }
  interior.userData.furnitureGroup = furnitureGroup;
  scene.add(interior);
  return interior;
}

function disposeGroupChildren(group: any) {
  while (group.children.length > 0) {
    const child = group.children[0];
    group.remove(child);
    child.traverse((object: any) => {
      if (object.geometry?.dispose) object.geometry.dispose();
      if (object.material) {
        const materials = Array.isArray(object.material) ? object.material : [object.material];
        for (const material of materials) {
          if (material.map) material.map.dispose();
          material.dispose?.();
        }
      }
    });
  }
}

function addConfiguredFurniture(parent: any, placement: RoomFurniturePlacement) {
  const item = new THREE.Group();
  item.position.set(placement.x, 0, 17.1 + placement.z);
  item.rotation.y = (placement.rotation * Math.PI) / 180;
  parent.add(item);

  switch (placement.kind) {
    case "desk":
      addDesk(item, 0, 0, 0x60b89c);
      break;
    case "chair":
      cylinder(item, 0.5, 0.52, 0.16, [0, 0.72, 0], 0x526c80, 16);
      box(item, [0.92, 0.95, 0.16], [0, 1.2, -0.42], 0x526c80);
      cylinder(item, 0.12, 0.15, 0.58, [0, 0.36, 0], 0x48596a, 10);
      break;
    case "plant":
      cylinder(item, 0.32, 0.36, 0.42, [0, 0.29, 0], 0xc17f55, 12);
      cylinder(item, 0.09, 0.04, 1.05, [0, 1.02, 0], 0x4f8b65, 8);
      sphere(item, 0.42, [0, 1.7, 0], 0x68a77a, [1.1, 1.2, 0.85]);
      sphere(item, 0.34, [0.28, 1.55, -0.12], 0x76b184, [1, 1.1, 0.9]);
      break;
    case "cabinet":
      box(item, [1.2, 1.7, 0.65], [0, 0.85, 0], 0x8b7765);
      box(item, [0.04, 1.45, 0.04], [-0.22, 0.85, 0.34], 0xe9d6ad);
      box(item, [0.04, 1.45, 0.04], [0.22, 0.85, 0.34], 0xe9d6ad);
      break;
    case "meeting_table":
      box(item, [2.6, 0.16, 1.4], [0, 0.95, 0], 0xc99564);
      for (const x of [-1.1, 1.1]) {
        for (const z of [-0.5, 0.5]) box(item, [0.12, 0.9, 0.12], [x, 0.45, z], 0x806044);
      }
      break;
  }
}

function applyRoomSceneConfig(furnitureGroup: any, config: WorldRoomSceneConfig) {
  disposeGroupChildren(furnitureGroup);
  for (const placement of config.furniture) addConfiguredFurniture(furnitureGroup, placement);
}

function hash(value: string) {
  let result = 0;
  for (let i = 0; i < value.length; i += 1) result = (result * 31 + value.charCodeAt(i)) | 0;
  return result;
}

type WalkBlocker = { x: number; z: number; halfWidth: number; halfDepth: number };

// Conservative ground-plane footprints for fixed office furniture. The player resolves
// X and Z independently so movement slides along furniture edges instead of tunnelling.
function getWalkBlockers(): WalkBlocker[] {
  const desks: WalkBlocker[] = DEPARTMENTS.flatMap((dept) =>
    [-2.15, 1.0].flatMap((zOffset) =>
      [-1.8, 1.8].map((xOffset) => ({
        x: dept.x + xOffset,
        z: dept.z + zOffset + 0.25,
        halfWidth: 1.68,
        halfDepth: 1.45,
      })),
    ),
  );
  return [
    ...desks,
    { x: 0, z: 0.1, halfWidth: 2.35, halfDepth: 0.95 }, // reception island
    { x: -8, z: 1.6, halfWidth: 2.25, halfDepth: 1.55 }, // sofa and arms
    { x: 0, z: 2.75, halfWidth: 0.95, halfDepth: 0.95 }, // coffee table
    { x: -11.5, z: 2.2, halfWidth: 0.82, halfDepth: 0.82 },
    { x: 11.5, z: 2.2, halfWidth: 0.82, halfDepth: 0.82 },
  ];
}

function canOccupyGround(x: number, z: number, blockers: WalkBlocker[], radius = 0.43): boolean {
  if (x < -16 || x > 16 || z < -10 || z > 9.2) return false;
  return !blockers.some((item) =>
    Math.abs(x - item.x) < item.halfWidth + radius &&
    Math.abs(z - item.z) < item.halfDepth + radius,
  );
}

function buildOffice(scene: any) {
  const floor = new THREE.Group();
  scene.add(floor);
  box(floor, [40, 0.5, 31], [0, -0.32, 0], 0x9a704e, { texture: "wood", roughness: 0.92 });
  // Batch the checkerboard planks into two instanced meshes to reduce hundreds of draw calls.
  const lightTiles = new THREE.InstancedMesh(
    new THREE.BoxGeometry(1.96, 0.025, 1.96),
    new THREE.MeshStandardMaterial({ color: 0xc99b6d, roughness: 0.78 }),
    150,
  );
  const darkTiles = new THREE.InstancedMesh(
    new THREE.BoxGeometry(1.96, 0.025, 1.96),
    new THREE.MeshStandardMaterial({ color: 0xb9895c, roughness: 0.78 }),
    150,
  );
  const tileTransform = new THREE.Object3D();
  let lightIndex = 0;
  let darkIndex = 0;
  for (let x = -19; x <= 19; x += 2) {
    for (let z = -14; z <= 14; z += 2) {
      tileTransform.position.set(x, -0.045, z);
      tileTransform.updateMatrix();
      if (Math.abs(x / 2 + z / 2) % 2 === 0) {
        lightTiles.setMatrixAt(lightIndex++, tileTransform.matrix);
      } else {
        darkTiles.setMatrixAt(darkIndex++, tileTransform.matrix);
      }
    }
  }
  lightTiles.castShadow = false;
  lightTiles.receiveShadow = false;
  darkTiles.castShadow = false;
  darkTiles.receiveShadow = false;
  lightTiles.instanceMatrix.needsUpdate = true;
  darkTiles.instanceMatrix.needsUpdate = true;
  floor.add(lightTiles, darkTiles);

  // Warm, compact office shell: rear windows and a wood floor establish a tycoon-office look.
  box(scene, [40, 4.8, 0.42], [0, 2.08, -15.05], 0xe8e4db, { texture: "plaster", roughness: 0.95 });
  for (let x = -17.5; x <= 17.5; x += 5) {
    box(scene, [3.9, 2.7, 0.08], [x, 2.55, -14.79], 0x9ec8dc, { roughness: 0.35, metalness: 0.05, emissive: 0x2c5364, emissiveIntensity: 0.08 });
    box(scene, [0.09, 2.9, 0.12], [x - 1.98, 2.55, -14.72], 0xf7f3e9);
    box(scene, [0.09, 2.9, 0.12], [x + 1.98, 2.55, -14.72], 0xf7f3e9);
  }
  // Horizontal glazing rails and fine mullions add scale to the rear windows.
  for (let x = -17.5; x <= 17.5; x += 5) {
    box(scene, [3.9, 0.075, 0.14], [x, 2.45, -14.67], 0xf7f3e9, { castShadow: false });
    box(scene, [3.9, 0.055, 0.14], [x, 3.73, -14.67], 0xf7f3e9, { castShadow: false });
    box(scene, [0.045, 2.55, 0.16], [x, 2.55, -14.63], 0x7e9eae, { castShadow: false });
    box(scene, [3.9, 0.11, 0.28], [x, 1.12, -14.57], 0xd5c8b4, { castShadow: false });
  }
  box(scene, [40, 0.18, 0.5], [0, 0.12, -14.72], 0xd1cfc6);

  // Low pastel department platforms make the floor plan readable without hiding the characters.
  for (const dept of DEPARTMENTS) {
    box(scene, [9.2, 0.12, 8.1], [dept.x, 0.03, dept.z], dept.color, { texture: "stone", roughness: 0.98 });
    const label = makeLabel(dept.name, "#ffffff");
    if (label) {
      label.position.set(dept.x, 3.9, dept.z - 3.35);
      label.scale.set(4.2, 1.05, 1);
      scene.add(label);
    }
    // Rounded-looking partitions and plant pots around each team area.
    box(scene, [8.8, 0.8, 0.16], [dept.x, 0.45, dept.z + 4], 0xb8b6ab);
    box(scene, [0.16, 0.8, 7.9], [dept.x - 4.5, 0.45, dept.z], 0xb8b6ab);
    // Keep decor in the back-right corner, away from the desk's chair and keyboard approach.
    const plantX = dept.x - 3.45;
    const plantZ = dept.z + 2.95;
    cylinder(scene, 0.38, 0.42, 0.52, [plantX, 0.32, plantZ], 0xc17f55, 12);
    cylinder(scene, 0.11, 0.05, 1.2, [plantX, 1.05, plantZ], 0x4f8b65, 8);
    sphere(scene, 0.5, [plantX - 0.3, 1.7, plantZ - 0.05], 0x68a77a, [1.1, 1.2, 0.85]);
    sphere(scene, 0.42, [plantX + 0.25, 1.55, plantZ + 0.2], 0x76b184, [1, 1.1, 0.9]);
    // A compact 2x2 workstation grid gives up to four employees a real desk/chair pair.
    for (const xOffset of [-1.8, 1.8]) {
      for (const zOffset of [-2.15, 1.0]) {
        addDesk(scene, dept.x + xOffset, dept.z + zOffset, dept.accent);
      }
    }
  }

  // A clear central circulation spine and inset team borders give the HQ a designed, game-like floor plan.
  box(scene, [30, 0.045, 2.8], [0, 0.11, -0.5], 0xd7d4c9, { castShadow: false, receiveShadow: false });
  box(scene, [29.8, 0.025, 0.1], [0, 0.145, -1.85], 0xb8b8b0, { castShadow: false, receiveShadow: false });
  box(scene, [29.8, 0.025, 0.1], [0, 0.145, 0.85], 0xb8b8b0, { castShadow: false, receiveShadow: false });

  // Department platforms receive a colored perimeter, corner markers and task-light fixtures.
  for (const dept of DEPARTMENTS) {
    const edgeY = 0.105;
    const edgeColor = dept.accent;
    box(scene, [9.1, 0.045, 0.12], [dept.x, edgeY, dept.z - 4.02], edgeColor, { emissive: edgeColor, emissiveIntensity: 0.08, castShadow: false });
    box(scene, [9.1, 0.045, 0.12], [dept.x, edgeY, dept.z + 4.02], edgeColor, { emissive: edgeColor, emissiveIntensity: 0.08, castShadow: false });
    box(scene, [0.12, 0.045, 7.95], [dept.x - 4.54, edgeY, dept.z], edgeColor, { emissive: edgeColor, emissiveIntensity: 0.08, castShadow: false });
    box(scene, [0.12, 0.045, 7.95], [dept.x + 4.54, edgeY, dept.z], edgeColor, { emissive: edgeColor, emissiveIntensity: 0.08, castShadow: false });

    // A subtle round meeting marker makes each team zone distinct without inventing activity metrics.
    const rug = new THREE.Mesh(
      new THREE.CircleGeometry(1.05, 32),
      new THREE.MeshStandardMaterial({ color: edgeColor, roughness: 0.94, transparent: true, opacity: 0.2 }),
    );
    rug.rotation.x = -Math.PI / 2;
    rug.position.set(dept.x - 3.05, 0.105, dept.z - 2.55);
    rug.receiveShadow = false;
    scene.add(rug);

    // Slim pendant rods and warm light housings add depth while keeping the top-down view open.
    box(scene, [0.055, 0.9, 0.055], [dept.x - 3.25, 3.35, dept.z - 2.85], 0x647487, { castShadow: false });
    box(scene, [0.9, 0.12, 0.42], [dept.x - 3.25, 2.86, dept.z - 2.85], 0xffe3a1, { emissive: 0xffc85a, emissiveIntensity: 0.35, castShadow: false });
  }

  // Window mullions and structural columns make the perimeter feel like a coherent office rather than a flat box.
  box(scene, [0.35, 4.7, 0.5], [-19.65, 2.05, 0], 0xe7e4dc);
  box(scene, [0.35, 4.7, 0.5], [19.65, 2.05, 0], 0xe7e4dc);
  for (const z of [-10, -2, 6, 13]) {
    box(scene, [0.3, 4.2, 0.34], [-19.35, 1.95, z], 0xd0d0c8);
    box(scene, [0.3, 4.2, 0.34], [19.35, 1.95, z], 0xd0d0c8);
  }

  // Framed abstract artwork on the side walls adds a finished office feel without covering the windows.
  for (const side of [-1, 1]) {
    for (const z of [-6, 2, 10]) {
      const x = side * 19.2;
      box(scene, [0.12, 1.05, 2.65], [x, 3.25, z], 0xf4efe4, { castShadow: false });
      box(scene, [0.06, 0.82, 2.42], [x + side * 0.07, 3.25, z], 0xc5d0d1, { castShadow: false });
      box(scene, [0.035, 0.12, 1.0], [x + side * 0.11, 3.43, z - 0.32], 0x7b9d9b, { castShadow: false });
      box(scene, [0.035, 0.12, 0.68], [x + side * 0.11, 3.16, z + 0.38], 0xd6ae78, { castShadow: false });
    }
  }

  // A warm inset border visually finishes the exposed front edge of the office floor.
  box(scene, [39.5, 0.08, 0.16], [0, -0.02, 15.28], 0xd5b58d, { castShadow: false, receiveShadow: false });
  box(scene, [0.16, 0.08, 30.5], [-19.9, -0.02, 0], 0xd5b58d, { castShadow: false, receiveShadow: false });
  box(scene, [0.16, 0.08, 30.5], [19.9, -0.02, 0], 0xd5b58d, { castShadow: false, receiveShadow: false });

  // A few compact lobby details establish scale and make the entrance read as a destination.
  for (const x of [-11.5, 11.5]) {
    // The lobby planters sit outside the sofa/reception footprint and preserve a clear approach.
    cylinder(scene, 0.52, 0.56, 0.38, [x, 0.27, 2.2], 0xb8a38b, 18);
    cylinder(scene, 0.1, 0.07, 1.25, [x, 1.05, 2.2], 0x4f8b65, 10);
    sphere(scene, 0.48, [x - 0.18, 1.78, 2.2], 0x6fa77b, [1, 1.12, 0.9]);
    sphere(scene, 0.38, [x + 0.2, 1.62, 2.38], 0x86b987, [1.05, 1.1, 0.9]);
  }

  // Reception island, sofa and meeting table add a recognizable HQ focal point.
  box(scene, [4.3, 0.45, 1.5], [0, 0.48, 0.1], 0x667f92);
  box(scene, [3.8, 0.16, 1.15], [0, 0.78, 0.1], 0xe6c18c);
  box(scene, [4.2, 0.9, 0.22], [-8, 0.52, 1.6], 0x8799a6, { texture: "fabric", roughness: 0.96 });
  box(scene, [1.1, 0.55, 2.5], [-9.55, 0.32, 1.5], 0x8799a6, { texture: "fabric", roughness: 0.96 });
  box(scene, [1.1, 0.55, 2.5], [-6.45, 0.32, 1.5], 0x8799a6, { texture: "fabric", roughness: 0.96 });
  // A circular inset rug and low coffee table soften the reception zone and distinguish it from desk rows.
  const lobbyRug = new THREE.Mesh(
    new THREE.CircleGeometry(3.1, 48),
    new THREE.MeshStandardMaterial({ color: 0x78949b, roughness: 0.96 }),
  );
  lobbyRug.rotation.x = -Math.PI / 2;
  lobbyRug.position.set(0, 0.08, 0.15);
  lobbyRug.receiveShadow = true;
  scene.add(lobbyRug);
  const lobbyRugInset = new THREE.Mesh(
    new THREE.RingGeometry(2.55, 2.68, 48),
    new THREE.MeshStandardMaterial({ color: 0xe1c49a, roughness: 0.9 }),
  );
  lobbyRugInset.rotation.x = -Math.PI / 2;
  lobbyRugInset.position.set(0, 0.09, 0.15);
  scene.add(lobbyRugInset);
  cylinder(scene, 0.72, 0.76, 0.16, [0, 0.28, 2.75], 0xc99564, 32);
  cylinder(scene, 0.14, 0.16, 0.24, [0, 0.1, 2.75], 0x806044, 16);
  cylinder(scene, 0.12, 0.12, 0.025, [0, 0.375, 2.75], 0xf1e4d0, 16);

  const title = makeLabel("AI COMPANY  •  HEADQUARTERS", "#f5d9a4");
  if (title) {
    title.position.set(0, 4.3, 0);
    title.scale.set(8.5, 1.5, 1);
    scene.add(title);
  }
}

export function WorldViewport({
  employees,
  selectedEmployeeId,
  onEmployeeSelect,
  onMapToggle: handleMapToggle,
  onRoomProximity,
  onRoomInteract,
  roomAccess,
}: {
  employees: WorldEmployee[];
  selectedEmployeeId: string | null;
  onEmployeeSelect: (employeeId: string | null) => void;
  onMapToggle: () => void;
  onRoomProximity: (near: boolean) => void;
  onRoomInteract: () => void;
  roomAccess: { granted: boolean; roomInstanceId: string | null; expiresAt: string | null; unavailable: boolean; sceneConfig: WorldRoomSceneConfig };
}) {
  const mountRef = useRef<HTMLDivElement>(null);
  const viewportRef = useRef<HTMLDivElement>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);
  useEffect(() => {
    const syncFullscreen = () => setIsFullscreen(document.fullscreenElement === viewportRef.current);
    document.addEventListener("fullscreenchange", syncFullscreen);
    return () => document.removeEventListener("fullscreenchange", syncFullscreen);
  }, []);

  const employeesRef = useRef(employees);
  const selectedEmployeeIdRef = useRef(selectedEmployeeId);
  const selectRef = useRef(onEmployeeSelect);
  const mapToggleRef = useRef(handleMapToggle);
  const roomProximityRef = useRef(onRoomProximity);
  const roomInteractRef = useRef(onRoomInteract);
  const roomAccessRef = useRef(roomAccess);

  useEffect(() => {
    employeesRef.current = employees;
    selectedEmployeeIdRef.current = selectedEmployeeId;
    selectRef.current = onEmployeeSelect;
    mapToggleRef.current = handleMapToggle;
    roomProximityRef.current = onRoomProximity;
    roomInteractRef.current = onRoomInteract;
    roomAccessRef.current = roomAccess;
  }, [employees, selectedEmployeeId, onEmployeeSelect, handleMapToggle, onRoomProximity, onRoomInteract, roomAccess]);

  useEffect(() => {
    const host = mountRef.current;
    if (!host) return;

    let renderer: any;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: "high-performance" });
    } catch {
      host.innerHTML = '<div class="flex h-full items-center justify-center bg-slate-900 p-8 text-center text-sm text-slate-300">This browser could not initialize WebGL. Update your graphics driver or enable hardware acceleration to view the 3D office.</div>';
      return;
    }

    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.12;
    renderer.domElement.setAttribute("aria-label", "AI Company World viewport");
    renderer.domElement.dataset.roomAccessState = "denied";
    renderer.domElement.removeAttribute("data-room-instance-id");
    renderer.domElement.setAttribute("role", "img");
    renderer.domElement.tabIndex = 0;
    renderer.domElement.style.display = "block";
    renderer.domElement.style.width = "100%";
    renderer.domElement.style.height = "100%";
    renderer.domElement.style.outline = "none";
    renderer.domElement.style.touchAction = "none";
    host.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x182331);
    scene.fog = new THREE.Fog(0x182331, 42, 86);

    const camera = new THREE.PerspectiveCamera(34, 1, 0.1, 220);
    const target = new THREE.Vector3(0, 0, 1.5);
    let distance = 35;
    const updateCamera = () => {
      // Keep the office's horizontal framing consistent on narrow portrait screens.
      // The world remains perspective/isometric; only the camera pull-back adapts to aspect ratio.
      const aspect = Math.max(0.35, camera.aspect || 1);
      // Keep desktop framing unchanged; portrait screens show a closer, pannable portion of the office.
      const responsiveScale = aspect < 1 ? 1.5 / aspect : 1;
      const effectiveDistance = distance * responsiveScale;
      const fogScale = effectiveDistance / distance;
      if (scene.fog instanceof THREE.Fog) {
        // Keep the scene visible when portrait framing pulls the camera back.
        scene.fog.near = 42 * fogScale;
        scene.fog.far = 86 * fogScale;
      }
      camera.position.set(target.x + effectiveDistance * 0.58, effectiveDistance * 1.08, target.z + effectiveDistance * 0.68);
      camera.lookAt(target.x, 0.8, target.z);
      camera.updateProjectionMatrix();
    };
    updateCamera();

    scene.add(new THREE.HemisphereLight(0xe9f2ff, 0x817968, 2.05));
    const sun = new THREE.DirectionalLight(0xffe4bd, 3.1);
    sun.position.set(-15, 28, 14);
    sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048);
    sun.shadow.camera.left = -32;
    sun.shadow.camera.right = 32;
    sun.shadow.camera.top = 32;
    sun.shadow.camera.bottom = -32;
    scene.add(sun);
    const fill = new THREE.DirectionalLight(0x8db7ff, 1.0);
    fill.position.set(18, 15, -20);
    scene.add(fill);

    buildOffice(scene);
    const ceoAvatar = addCEOAvatar(scene);
    const walkBlockers = getWalkBlockers();
    const roomEntrance = addLockedRoom(scene);
    const roomInterior = addAuthorizedRoomInterior(scene);
    const roomFurnitureGroup = roomInterior.userData.furnitureGroup;
    let renderedRoomInstanceId: string | null = null;
    let renderedSceneConfigKey = "";
    let wasNearRoom = false;
    const workers: WorkerVisual[] = [];
    let signature = "";
    const syncWorkers = () => {
      const next = employeesRef.current;
      const nextSignature = next.map((e) => [e.id, e.name, e.state, e.slot].join(":")).join("|");
      if (signature === nextSignature) return;
      for (const worker of workers) {
        scene.remove(worker.group);
        worker.group.traverse((object: any) => {
          if (object.geometry?.dispose) object.geometry.dispose();
          if (object.material) {
            const materials = Array.isArray(object.material) ? object.material : [object.material];
            for (const material of materials) {
              if (material.map) material.map.dispose();
              material.dispose?.();
            }
          }
        });
      }
      workers.length = 0;
      // Match each employee to an actual desk/chair assembly; characters face -Z.
      const desks: [number, number][] = DEPARTMENTS.flatMap((dept) =>
        [-2.15, 1.0].flatMap((zOffset) =>
          [-1.8, 1.8].map((xOffset) => [dept.x + xOffset, dept.z + zOffset + 1.05] as [number, number]),
        ),
      );
      next.forEach((employee, index) => {
        const worker = addWorker(scene, employee);
        if (index < desks.length) {
          const place = desks[index];
          worker.group.position.set(place[0], 0, place[1]);
        } else {
          // Employees beyond the 20 authored stations wait in a separate front staging row
          // rather than being silently stacked into occupied workstations.
          const overflowIndex = index - desks.length;
          const column = overflowIndex % 7;
          const row = Math.floor(overflowIndex / 7);
          worker.group.position.set(-18 + column * 6, 0, 11.5 + row * 1.25);
        }
        worker.group.rotation.y = Math.PI + 0.2;
        worker.group.userData.homePosition = worker.group.position.clone();
        worker.group.userData.homeRotationY = worker.group.rotation.y;
        workers.push(worker);
      });
      signature = nextSignature;
    };
    syncWorkers();

    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    const cameraInput = new WorldInput(renderer.domElement);
    let frame = 0;
    let last = performance.now();
    let isRendering = !document.hidden;
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    let mobileMove = { x: 0, y: 0 };

    const onPan = (event: Event) => {
      const { dx, dy } = (event as CustomEvent<{ dx: number; dy: number }>).detail;
      // Convert screen-space dragging into the camera's ground-plane basis.
      // Mapping screen X directly to world X and screen Y to world Z made the
      // office slide diagonally relative to the pointer at this camera angle.
      const rect = renderer.domElement.getBoundingClientRect();
      const cameraDistance = camera.position.distanceTo(new THREE.Vector3(target.x, 0.8, target.z));
      const worldPerPixel =
        (2 * cameraDistance * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2))) /
        Math.max(1, rect.height);
      const cameraRight = new THREE.Vector3(1, 0, 0).applyQuaternion(camera.quaternion);
      cameraRight.y = 0;
      cameraRight.normalize();
      const cameraUp = new THREE.Vector3(0, 1, 0).applyQuaternion(camera.quaternion);
      cameraUp.y = 0;
      cameraUp.normalize();
      const pan = screenPanToWorldDelta(
        dx,
        dy,
        worldPerPixel,
        { x: cameraRight.x, z: cameraRight.z },
        { x: cameraUp.x, z: cameraUp.z },
      );
      target.x += pan.x;
      target.z += pan.z;
      updateCamera();
    };
    const onReset = () => {
      target.set(0, 0, 0);
      distance = 35;
      updateCamera();
    };
    const onZoom = (event: Event) => {
      const { delta } = (event as CustomEvent<{ delta: number }>).detail;
      distance = Math.max(11, Math.min(92, distance * (1 - delta)));
      updateCamera();
    };
    const onMapToggle = () => mapToggleRef.current();
    const onRoomInteractEvent = () => { if (wasNearRoom) roomInteractRef.current(); };
    const onMobileMove = (event: Event) => {
      mobileMove = (event as CustomEvent<{ x: number; y: number }>).detail;
    };
    const onTap = (event: Event) => {
      const { x, y } = (event as CustomEvent<{ x: number; y: number }>).detail;
      const rect = renderer.domElement.getBoundingClientRect();
      pointer.x = (x / rect.width) * 2 - 1;
      pointer.y = -(y / rect.height) * 2 + 1;
      raycaster.setFromCamera(pointer, camera);
      const hits = raycaster.intersectObjects(workers.map((worker) => worker.hit), false);
      selectRef.current(hits[0]?.object.userData.employeeId ?? null);
    };

    renderer.domElement.addEventListener("world:pan", onPan);
    renderer.domElement.addEventListener("world:zoom", onZoom);
    renderer.domElement.addEventListener("world:reset", onReset);
    renderer.domElement.addEventListener("world:tap", onTap);
    renderer.domElement.addEventListener("world:map-toggle", onMapToggle);
    renderer.domElement.addEventListener("world:interact", onRoomInteractEvent);
    host.addEventListener("world:mobilemove", onMobileMove);

    const observer = new ResizeObserver(() => {
      const width = Math.max(1, host.clientWidth);
      const height = Math.max(1, host.clientHeight);
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      updateCamera();
    });
    observer.observe(host);
    renderer.setSize(Math.max(1, host.clientWidth), Math.max(1, host.clientHeight), false);
    camera.aspect = Math.max(1, host.clientWidth) / Math.max(1, host.clientHeight);
    camera.updateProjectionMatrix();

    const tick = (now: number) => {
      if (!isRendering) return;
      const delta = Math.min(64, now - last);
      last = now;
      syncWorkers();
      const keyboard = cameraInput.consume();
      const moveX = keyboard.moveX || mobileMove.x;
      const moveY = keyboard.moveY || mobileMove.y;
      const seconds = delta / 1000;
      const inputLength = Math.hypot(moveX, moveY);
      const desiredX = inputLength > 0 ? (moveX / inputLength) * 6.2 : 0;
      const desiredZ = inputLength > 0 ? (moveY / inputLength) * 6.2 : 0;
      const velocity = ceoAvatar.userData.velocity ?? (ceoAvatar.userData.velocity = new THREE.Vector2());
      const responsiveness = inputLength > 0 ? 12 : 14;
      velocity.lerp(new THREE.Vector2(desiredX, desiredZ), Math.min(1, seconds * responsiveness));
      const speed = velocity.length();
      if (speed > 0.025) {
        const nextX = ceoAvatar.position.x + velocity.x * seconds;
        const nextZ = ceoAvatar.position.z + velocity.y * seconds;
        // Axis-separated collision permits wall-sliding and prevents crossing fixed furniture.
        if (canOccupyGround(nextX, ceoAvatar.position.z, walkBlockers)) ceoAvatar.position.x = nextX;
        if (canOccupyGround(ceoAvatar.position.x, nextZ, walkBlockers)) ceoAvatar.position.z = nextZ;
        const desiredRotation = Math.atan2(velocity.x, velocity.y);
        const rotationDelta = Math.atan2(Math.sin(desiredRotation - ceoAvatar.rotation.y), Math.cos(desiredRotation - ceoAvatar.rotation.y));
        ceoAvatar.rotation.y += rotationDelta * Math.min(1, seconds * 10);
      }
      target.x += (ceoAvatar.position.x - target.x) * Math.min(1, seconds * 8);
      target.z += (ceoAvatar.position.z - 2.5 - target.z) * Math.min(1, seconds * 8);
      updateCamera();

      const walkRig = ceoAvatar.userData.walkRig;
      if (walkRig) {
        const walking = speed > 0.22 && !reducedMotion.matches;
        ceoAvatar.userData.walkPhase += speed * seconds * 3.1;
        const phase = ceoAvatar.userData.walkPhase;
        const swing = walking ? Math.sin(phase) * 0.48 : 0;
        walkRig.leftLeg.rotation.x += (swing - walkRig.leftLeg.rotation.x) * Math.min(1, seconds * 12);
        walkRig.rightLeg.rotation.x += (-swing - walkRig.rightLeg.rotation.x) * Math.min(1, seconds * 12);
        walkRig.leftArm.rotation.x += (-swing * 0.72 - walkRig.leftArm.rotation.x) * Math.min(1, seconds * 12);
        walkRig.rightArm.rotation.x += (swing * 0.72 - walkRig.rightArm.rotation.x) * Math.min(1, seconds * 12);
        const bodyBob = walking ? Math.abs(Math.sin(phase * 2)) * 0.045 : 0;
        ceoAvatar.position.y += (bodyBob - ceoAvatar.position.y) * Math.min(1, seconds * 14);
      }
      const nearRoom = Math.hypot(ceoAvatar.position.x, ceoAvatar.position.z - 9.4) < 3.1;
      if (nearRoom !== wasNearRoom) { wasNearRoom = nearRoom; roomProximityRef.current(nearRoom); }

      // Re-evaluate the lease every frame so expiry or a query error closes the room immediately.
      const access = roomAccessRef.current;
      const roomGranted = isRoomSceneAccessUsable(access, access.unavailable);
      const authorizedInstanceId = roomGranted ? access.roomInstanceId : null;
      if (authorizedInstanceId !== renderedRoomInstanceId) {
        renderedRoomInstanceId = authorizedInstanceId;
        roomInterior.userData.roomInstanceId = authorizedInstanceId;
      }
      const sceneConfigKey = authorizedInstanceId ? `${authorizedInstanceId}:${JSON.stringify(access.sceneConfig)}` : "";
      if (roomGranted && authorizedInstanceId && sceneConfigKey !== renderedSceneConfigKey) {
        applyRoomSceneConfig(roomFurnitureGroup, access.sceneConfig);
        renderedSceneConfigKey = sceneConfigKey;
      }
      roomInterior.visible = roomGranted && roomInterior.userData.roomInstanceId === authorizedInstanceId;
      renderer.domElement.dataset.roomFurnitureCount = roomInterior.visible ? String(roomFurnitureGroup.children.length) : "0";
      renderer.domElement.dataset.roomEmployeeCount = roomInterior.visible ? String(access.sceneConfig.employee_placements.length) : "0";
      renderer.domElement.dataset.roomAccessState = roomInterior.visible ? "granted" : "denied";
      if (roomInterior.visible && authorizedInstanceId) renderer.domElement.dataset.roomInstanceId = authorizedInstanceId;
      else renderer.domElement.removeAttribute("data-room-instance-id");
      roomEntrance.userData.door.rotation.y = roomGranted ? Math.PI / 2 : 0;
      if (roomEntrance.userData.doorway) roomEntrance.userData.doorway.visible = !roomGranted;
      if (roomEntrance.userData.lockedLabel) roomEntrance.userData.lockedLabel.visible = !roomGranted;
      if (roomEntrance.userData.activeLabel) roomEntrance.userData.activeLabel.visible = roomGranted;

      for (const worker of workers) {
        const selected = worker.id === selectedEmployeeIdRef.current;
        const employeePlacement = roomInterior.visible
          ? access.sceneConfig.employee_placements.find((placement) => placement.employee_id === worker.id)
          : undefined;
        const homePosition = worker.group.userData.homePosition;
        if (employeePlacement) {
          worker.group.position.set(employeePlacement.x, 0, 17.1 + employeePlacement.z);
          worker.group.rotation.y = (employeePlacement.rotation * Math.PI) / 180;
        } else if (homePosition) {
          worker.group.position.copy(homePosition);
          worker.group.rotation.y = worker.group.userData.homeRotationY ?? Math.PI + 0.2;
        }
        worker.ring.material.color.setHex(selected ? 0x4fd1c5 : 0xffffff);
        worker.ring.material.opacity = selected ? 1 : 0.28;
        worker.ring.scale.setScalar(selected ? 1.14 : 1);
        worker.status.material.color.setHex(STATE_COLOR[worker.state as WorldEmployee["state"]] ?? 0x9aa8bb);
        worker.status.material.emissive.setHex(STATE_COLOR[worker.state as WorldEmployee["state"]] ?? 0x9aa8bb);
        worker.group.position.y = 0;
        const activityPulse = worker.state === "WORKING" && !reducedMotion.matches
          ? 1 + (Math.sin(now * 0.003 + (Math.abs(hash(worker.id)) % 20)) + 1) * 0.06
          : 1;
        worker.status.scale.setScalar(activityPulse);
        worker.status.material.emissiveIntensity = worker.state === "WORKING" && !reducedMotion.matches
          ? 0.28 + (activityPulse - 1) * 0.8
          : 0.18;

        const workRig = worker.group.userData.workRig;
        if (workRig) {
          const typing = worker.state === "WORKING" && !reducedMotion.matches
            ? Math.sin(now * 0.009 + workRig.phase) * 0.055
            : 0;
          const settle = Math.min(1, seconds * 10);
          workRig.leftSleeve.rotation.x += (workRig.baseLeftSleeveX + typing - workRig.leftSleeve.rotation.x) * settle;
          workRig.rightSleeve.rotation.x += (workRig.baseRightSleeveX - typing - workRig.rightSleeve.rotation.x) * settle;
          workRig.leftArm.rotation.x += (workRig.baseLeftArmX + typing * 0.8 - workRig.leftArm.rotation.x) * settle;
          workRig.rightArm.rotation.x += (workRig.baseRightArmX - typing * 0.8 - workRig.rightArm.rotation.x) * settle;
        }
      }
      renderer.render(scene, camera);
      frame = requestAnimationFrame(tick);
    };
    const onVisibilityChange = () => {
      if (document.hidden) {
        isRendering = false;
        cancelAnimationFrame(frame);
        return;
      }
      isRendering = true;
      last = performance.now();
      frame = requestAnimationFrame(tick);
    };
    document.addEventListener("visibilitychange", onVisibilityChange);
    if (isRendering) frame = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(frame);
      document.removeEventListener("visibilitychange", onVisibilityChange);
      observer.disconnect();
      cameraInput.destroy();
      renderer.domElement.removeEventListener("world:pan", onPan);
      renderer.domElement.removeEventListener("world:zoom", onZoom);
      renderer.domElement.removeEventListener("world:reset", onReset);
      renderer.domElement.removeEventListener("world:tap", onTap);
      renderer.domElement.removeEventListener("world:map-toggle", onMapToggle);
      renderer.domElement.removeEventListener("world:interact", onRoomInteractEvent);
      host.removeEventListener("world:mobilemove", onMobileMove);
      scene.traverse((object: any) => {
        if (object.geometry?.dispose) object.geometry.dispose();
        if (object.material) {
          const materials = Array.isArray(object.material) ? object.material : [object.material];
          for (const material of materials) {
            if (material.map) material.map.dispose();
            material.dispose?.();
          }
        }
      });
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, []);

  return (
    <div ref={viewportRef} className={`world-viewport relative w-full overflow-hidden bg-slate-900 shadow-2xl ${isFullscreen ? "world-viewport-fullscreen h-screen rounded-none border-0" : "min-h-[420px] rounded-2xl border border-slate-700/80"}`} style={{ height: isFullscreen ? "100dvh" : "min(80vh, 900px)" }}>
      <div ref={mountRef} className="absolute inset-0" />
      <div className="sr-only" aria-label="Office employees">
        {employees.map((employee) => (
          <button
            key={employee.id}
            type="button"
            aria-label={`Select ${employee.name}`}
            aria-pressed={selectedEmployeeId === employee.id}
            onClick={() => onEmployeeSelect(employee.id)}
          >
            {employee.name} — {employee.state}
          </button>
        ))}
      </div>
      <div className="pointer-events-none absolute inset-x-0 top-0 h-24 bg-gradient-to-b from-slate-950/60 to-transparent" />
      <div className="z-10 flex gap-1 rounded-xl border border-white/10 bg-slate-950/90 p-1 backdrop-blur" style={{ position: "absolute", left: 16, bottom: 16, maxWidth: "calc(100% - 32px)" }} aria-label="World camera controls">
        <button type="button" className="h-8 w-8 rounded-lg text-sm text-slate-200 hover:bg-white/10" onClick={() => mountRef.current?.querySelector("canvas")?.dispatchEvent(new CustomEvent("world:zoom", { detail: { delta: 0.12 } }))} aria-label="Zoom in">+</button>
        <button type="button" className="h-8 w-8 rounded-lg text-sm text-slate-200 hover:bg-white/10" onClick={() => mountRef.current?.querySelector("canvas")?.dispatchEvent(new CustomEvent("world:zoom", { detail: { delta: -0.12 } }))} aria-label="Zoom out">−</button>
        <button type="button" className="rounded-lg px-2 text-xs text-slate-300 hover:bg-white/10" onClick={() => mountRef.current?.querySelector("canvas")?.dispatchEvent(new CustomEvent("world:reset"))}>Reset view</button>
        <button type="button" className="rounded-lg px-2 text-xs text-slate-100 hover:bg-white/10" onClick={() => { if (document.fullscreenElement === viewportRef.current) { void document.exitFullscreen(); } else { void viewportRef.current?.requestFullscreen(); } }} aria-label={isFullscreen ? "Exit fullscreen world view" : "Show world in fullscreen"} aria-pressed={isFullscreen}>{isFullscreen ? "⤢ Exit full screen" : "⛶ Full screen"}</button>
      </div>
      <div className="pointer-events-none rounded-xl border border-white/10 bg-slate-950/85 px-3 py-2 text-xs text-slate-200 backdrop-blur" style={{ position: "absolute", left: 16, top: 16, maxWidth: "calc(100% - 32px)" }}>
        <div className="font-semibold tracking-wide text-amber-100">AI COMPANY HQ</div>
        <div className="mt-1 hidden sm:block text-slate-300">WASD / arrows · drag to pan · wheel to zoom</div>
        <div className="mt-1 sm:hidden text-slate-300">Joystick · drag to pan</div>
      </div>
      <div className="pointer-events-none rounded-xl border border-white/10 bg-slate-950/85 px-3 py-2 text-xs text-slate-300 backdrop-blur" style={{ position: "absolute", right: 16, top: 16, maxWidth: "calc(100% - 32px)" }}>
        <span className="mr-2 inline-block h-2 w-2 rounded-full bg-emerald-400" />Working
        <span className="mx-2 text-slate-500">•</span>
        <span className="mr-2 inline-block h-2 w-2 rounded-full bg-amber-400" />Approval
      </div>
    </div>
  );
}
