"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";
import { WorldInput } from "./WorldInput";
import type { WorldEmployee } from "./WorldState";

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

function box(
  parent: any,
  size: [number, number, number],
  position: [number, number, number],
  color: number,
  options: { roughness?: number; metalness?: number; emissive?: number; emissiveIntensity?: number } = {},
) {
  const mesh = new THREE.Mesh(
    new THREE.BoxGeometry(...size),
    new THREE.MeshStandardMaterial({ color, roughness: options.roughness ?? 0.78, metalness: options.metalness ?? 0, emissive: options.emissive ?? 0, emissiveIntensity: options.emissiveIntensity ?? 0 }),
  );
  mesh.position.set(...position);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
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
  box(desk, [3.15, 0.18, 1.65], [0, 1.32, 0], 0xc99564);
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
  box(chair, [0.92, 0.95, 0.16], [0, 1.2, 0.42], 0x526c80);
  cylinder(chair, 0.12, 0.15, 0.58, [0, 0.36, 0], 0x48596a, 10);
  return desk;
}

function addWorker(parent: any, employee: WorldEmployee): WorkerVisual {
  // A seated, desk-facing character reads more like an office-management game than a standing token.
  const group = new THREE.Group();
  group.userData.employeeId = employee.id;
  parent.add(group);

  const palette = [0x557ca5, 0x6b9b82, 0xc78360, 0x8b78b6, 0x4e9aab, 0xc28b4c];
  const color = palette[Math.abs(hash(employee.id)) % palette.length];

  // Compact stylized body, positioned in the chair in front of the monitor.
  cylinder(group, 0.34, 0.42, 0.78, [0, 1.0, 0.02], color, 14);
  sphere(group, 0.34, [0, 1.67, -0.02], 0xf0c8a5, [1, 1.03, 0.96]);
  sphere(group, 0.37, [0, 1.86, -0.08], 0x51413b, [1, 0.52, 0.95]);
  sphere(group, 0.045, [-0.115, 1.68, 0.285], 0x26313a, [0.8, 1, 0.5]);
  sphere(group, 0.045, [0.115, 1.68, 0.285], 0x26313a, [0.8, 1, 0.5]);

  // Bent legs and small shoes create a seated silhouette.
  cylinder(group, 0.14, 0.15, 0.42, [-0.2, 0.48, 0.05], 0x33445b, 10).rotation.x = Math.PI / 2;
  cylinder(group, 0.14, 0.15, 0.42, [0.2, 0.48, 0.05], 0x33445b, 10).rotation.x = Math.PI / 2;
  box(group, [0.25, 0.13, 0.34], [-0.2, 0.2, 0.3], 0x293545);
  box(group, [0.25, 0.13, 0.34], [0.2, 0.2, 0.3], 0x293545);

  // Arms angle toward the desk so the employee appears to be using the workstation.
  const leftArm = cylinder(group, 0.095, 0.12, 0.48, [-0.31, 1.12, 0.17], 0xf0c8a5, 10);
  leftArm.rotation.x = 0.72;
  leftArm.rotation.z = -0.24;
  const rightArm = cylinder(group, 0.095, 0.12, 0.48, [0.31, 1.12, 0.17], 0xf0c8a5, 10);
  rightArm.rotation.x = 0.72;
  rightArm.rotation.z = 0.24;

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

function hash(value: string) {
  let result = 0;
  for (let i = 0; i < value.length; i += 1) result = (result * 31 + value.charCodeAt(i)) | 0;
  return result;
}

function buildOffice(scene: any) {
  const floor = new THREE.Group();
  scene.add(floor);
  box(floor, [40, 0.5, 31], [0, -0.32, 0], 0x9a704e);
  for (let x = -19; x <= 19; x += 2) {
    for (let z = -14; z <= 14; z += 2) {
      box(floor, [1.96, 0.025, 1.96], [x, -0.045, z], (Math.abs(x / 2 + z / 2) % 2 === 0) ? 0xc99b6d : 0xb9895c);
    }
  }

  // Warm, compact office shell: rear windows and a wood floor establish a tycoon-office look.
  box(scene, [40, 4.8, 0.42], [0, 2.08, -15.05], 0xe7e4dc);
  for (let x = -17.5; x <= 17.5; x += 5) {
    box(scene, [3.9, 2.7, 0.08], [x, 2.55, -14.79], 0x9ec8dc, { roughness: 0.35, metalness: 0.05, emissive: 0x2c5364, emissiveIntensity: 0.08 });
    box(scene, [0.09, 2.9, 0.12], [x - 1.98, 2.55, -14.72], 0xf7f3e9);
    box(scene, [0.09, 2.9, 0.12], [x + 1.98, 2.55, -14.72], 0xf7f3e9);
  }
  box(scene, [40, 0.18, 0.5], [0, 0.12, -14.72], 0xd1cfc6);

  // Low pastel department platforms make the floor plan readable without hiding the characters.
  for (const dept of DEPARTMENTS) {
    box(scene, [9.2, 0.12, 8.1], [dept.x, 0.03, dept.z], dept.color);
    const label = makeLabel(dept.name, "#ffffff");
    if (label) {
      label.position.set(dept.x, 3.9, dept.z - 3.35);
      label.scale.set(4.2, 1.05, 1);
      scene.add(label);
    }
    // Rounded-looking partitions and plant pots around each team area.
    box(scene, [8.8, 0.8, 0.16], [dept.x, 0.45, dept.z + 4], 0xb8b6ab);
    box(scene, [0.16, 0.8, 7.9], [dept.x - 4.5, 0.45, dept.z], 0xb8b6ab);
    cylinder(scene, 0.38, 0.42, 0.52, [dept.x + 3.55, 0.32, dept.z + 2.75], 0xc17f55, 12);
    cylinder(scene, 0.11, 0.05, 1.2, [dept.x + 3.55, 1.05, dept.z + 2.75], 0x4f8b65, 8);
    sphere(scene, 0.5, [dept.x + 3.25, 1.7, dept.z + 2.7], 0x68a77a, [1.1, 1.2, 0.85]);
    sphere(scene, 0.42, [dept.x + 3.8, 1.55, dept.z + 2.45], 0x76b184, [1, 1.1, 0.9]);
    addDesk(scene, dept.x - 1.65, dept.z - 0.2, dept.accent);
    addDesk(scene, dept.x + 1.65, dept.z + 1.5, dept.accent);
  }

  // Reception island, sofa and meeting table add a recognizable HQ focal point.
  box(scene, [4.3, 0.45, 1.5], [0, 0.48, 0.1], 0x667f92);
  box(scene, [3.8, 0.16, 1.15], [0, 0.78, 0.1], 0xe6c18c);
  box(scene, [4.2, 0.9, 0.22], [-8, 0.52, 1.6], 0x6e8999);
  box(scene, [1.1, 0.55, 2.5], [-9.55, 0.32, 1.5], 0x809aab);
  box(scene, [1.1, 0.55, 2.5], [-6.45, 0.32, 1.5], 0x809aab);
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
}: {
  employees: WorldEmployee[];
  selectedEmployeeId: string | null;
  onEmployeeSelect: (employeeId: string | null) => void;
  onMapToggle: () => void;
}) {
  const mountRef = useRef<HTMLDivElement>(null);
  const employeesRef = useRef(employees);
  const selectedEmployeeIdRef = useRef(selectedEmployeeId);
  const selectRef = useRef(onEmployeeSelect);
  const mapToggleRef = useRef(handleMapToggle);

  useEffect(() => {
    employeesRef.current = employees;
    selectedEmployeeIdRef.current = selectedEmployeeId;
    selectRef.current = onEmployeeSelect;
    mapToggleRef.current = handleMapToggle;
  }, [employees, selectedEmployeeId, onEmployeeSelect, handleMapToggle]);

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

    const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 180);
    const target = new THREE.Vector3(0, 0, 0);
    let distance = 43;
    const updateCamera = () => {
      camera.position.set(target.x + distance * 0.58, distance * 1.08, target.z + distance * 0.68);
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
      const desks: [number, number][] = DEPARTMENTS.flatMap((dept) => [
        [dept.x - 1.65, dept.z - 0.2 + 1.35] as [number, number],
        [dept.x + 1.65, dept.z + 1.5 + 1.35] as [number, number],
      ]);
      next.forEach((employee, index) => {
        const worker = addWorker(scene, employee);
        const place = desks[index % desks.length];
        const extraRow = Math.floor(index / desks.length);
        worker.group.position.set(place[0], 0, place[1] + extraRow * 2.3);
        worker.group.rotation.y = Math.PI + 0.2;
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
    let mobileMove = { x: 0, y: 0 };

    const onPan = (event: Event) => {
      const { dx, dy } = (event as CustomEvent<{ dx: number; dy: number }>).detail;
      const scale = distance * 0.00135;
      target.x -= dx * scale;
      target.z -= dy * scale;
      updateCamera();
    };
    const onReset = () => {
      target.set(0, 0, 0);
      distance = 43;
      updateCamera();
    };
    const onZoom = (event: Event) => {
      const { delta } = (event as CustomEvent<{ delta: number }>).detail;
      distance = Math.max(25, Math.min(66, distance * (1 - delta)));
      updateCamera();
    };
    const onMapToggle = () => mapToggleRef.current();
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
    host.addEventListener("world:mobilemove", onMobileMove);

    const observer = new ResizeObserver(() => {
      const width = Math.max(1, host.clientWidth);
      const height = Math.max(1, host.clientHeight);
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    });
    observer.observe(host);
    renderer.setSize(Math.max(1, host.clientWidth), Math.max(1, host.clientHeight), false);
    camera.aspect = Math.max(1, host.clientWidth) / Math.max(1, host.clientHeight);
    camera.updateProjectionMatrix();

    const tick = (now: number) => {
      const delta = Math.min(64, now - last);
      last = now;
      syncWorkers();
      const keyboard = cameraInput.consume();
      const moveX = keyboard.moveX || mobileMove.x;
      const moveY = keyboard.moveY || mobileMove.y;
      if (moveX || moveY) {
        const length = Math.hypot(moveX, moveY) || 1;
        target.x += (moveX / length) * delta * 0.008 * distance / 2;
        target.z += (moveY / length) * delta * 0.008 * distance / 2;
        updateCamera();
      }
      for (const worker of workers) {
        const selected = worker.id === selectedEmployeeIdRef.current;
        worker.ring.material.color.setHex(selected ? 0x4fd1c5 : 0xffffff);
        worker.ring.material.opacity = selected ? 1 : 0.28;
        worker.ring.scale.setScalar(selected ? 1.14 : 1);
        worker.status.material.color.setHex(STATE_COLOR[worker.state as WorldEmployee["state"]] ?? 0x9aa8bb);
        worker.status.material.emissive.setHex(STATE_COLOR[worker.state as WorldEmployee["state"]] ?? 0x9aa8bb);
        worker.group.position.y = 0;
        const activityPulse = worker.state === "WORKING" ? 1 + (Math.sin(now * 0.003 + (Math.abs(hash(worker.id)) % 20)) + 1) * 0.06 : 1;
        worker.status.scale.setScalar(activityPulse);
        worker.status.material.emissiveIntensity = worker.state === "WORKING" ? 0.28 + (activityPulse - 1) * 0.8 : 0.18;
      }
      renderer.render(scene, camera);
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      cameraInput.destroy();
      renderer.domElement.removeEventListener("world:pan", onPan);
      renderer.domElement.removeEventListener("world:zoom", onZoom);
      renderer.domElement.removeEventListener("world:reset", onReset);
      renderer.domElement.removeEventListener("world:tap", onTap);
      renderer.domElement.removeEventListener("world:map-toggle", onMapToggle);
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
    <div className="relative min-h-[420px] w-full overflow-hidden rounded-2xl border border-slate-700/80 bg-slate-900 shadow-2xl" style={{ height: "min(72vh, 760px)" }}>
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
      <div className="absolute bottom-4 left-4 z-10 flex gap-1 rounded-xl border border-white/10 bg-slate-950/80 p-1 backdrop-blur" aria-label="World camera controls">
        <button type="button" className="h-8 w-8 rounded-lg text-sm text-slate-200 hover:bg-white/10" onClick={() => mountRef.current?.querySelector("canvas")?.dispatchEvent(new CustomEvent("world:zoom", { detail: { delta: 0.12 } }))} aria-label="Zoom in">+</button>
        <button type="button" className="h-8 w-8 rounded-lg text-sm text-slate-200 hover:bg-white/10" onClick={() => mountRef.current?.querySelector("canvas")?.dispatchEvent(new CustomEvent("world:zoom", { detail: { delta: -0.12 } }))} aria-label="Zoom out">−</button>
        <button type="button" className="rounded-lg px-2 text-xs text-slate-300 hover:bg-white/10" onClick={() => mountRef.current?.querySelector("canvas")?.dispatchEvent(new CustomEvent("world:reset"))}>Reset view</button>
      </div>
      <div className="pointer-events-none absolute left-4 top-4 rounded-xl border border-white/10 bg-slate-950/75 px-3 py-2 text-xs text-slate-200 backdrop-blur">
        <div className="font-semibold tracking-wide text-amber-100">AI COMPANY HQ</div>
        <div className="mt-1 hidden sm:block text-slate-300">WASD / arrows · drag to pan · wheel to zoom</div>
        <div className="mt-1 sm:hidden text-slate-300">Joystick · drag to pan</div>
      </div>
      <div className="pointer-events-none absolute right-4 top-4 rounded-xl border border-white/10 bg-slate-950/75 px-3 py-2 text-xs text-slate-300 backdrop-blur">
        <span className="mr-2 inline-block h-2 w-2 rounded-full bg-emerald-400" />Working
        <span className="mx-2 text-slate-500">•</span>
        <span className="mr-2 inline-block h-2 w-2 rounded-full bg-amber-400" />Approval
      </div>
    </div>
  );
}
