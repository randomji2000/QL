import { useEffect, useRef } from 'react'
import * as THREE from 'three'

interface Props {
  x: number
  y: number
  z: number
  size?: number
  color?: string
}

const RADIUS = 1

export default function BlochSphere({ x, y, z, size = 170, color = '#7c6cf0' }: Props) {
  const mount = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = mount.current
    if (!el) return

    const scene = new THREE.Scene()
    const world = new THREE.Group()
    scene.add(world)
    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100)
    camera.position.set(2.6, 2.0, 3.2)
    camera.lookAt(0, 0, 0)

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    el.appendChild(renderer.domElement)
    const width = size
    renderer.setSize(width, width)

    // Wireframe sphere
    const sphere = new THREE.Mesh(
      new THREE.SphereGeometry(RADIUS, 32, 16),
      new THREE.MeshBasicMaterial({ color: 0x2a3567, wireframe: true, transparent: true, opacity: 0.85 }),
    )
    world.add(sphere)

    // Semi-transparent shell
    const shell = new THREE.Mesh(
      new THREE.SphereGeometry(RADIUS, 24, 16),
      new THREE.MeshBasicMaterial({ color: 0x3a4690, transparent: true, opacity: 0.06, depthWrite: false }),
    )
    world.add(shell)

    // Axis lines
    const axis = (dir: [number, number, number], c: number) => {
      const g = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(-dir[0], -dir[1], -dir[2]).multiplyScalar(RADIUS),
        new THREE.Vector3(dir[0], dir[1], dir[2]).multiplyScalar(RADIUS),
      ])
      world.add(new THREE.Line(g, new THREE.LineBasicMaterial({ color: c })))
    }
    axis([1, 0, 0], 0xef5350) // X
    axis([0, 1, 0], 0x66bb6a) // Y
    axis([0, 0, 1], 0x42a5f5) // Z

    // |0> / |1> caps
    const cap = (p: [number, number, number], c: number) => {
      const dot = new THREE.Mesh(new THREE.SphereGeometry(0.045, 12, 12), new THREE.MeshBasicMaterial({ color: c }))
      dot.position.set(p[0], p[1], p[2])
      world.add(dot)
    }
    cap([0, 0, 1], 0x42a5f5)
    cap([0, 0, -1], 0xef8b8b)

    // Equator ring
    const ring = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(
        Array.from({ length: 65 }, (_, i) => {
          const a = (i / 64) * Math.PI * 2
          return new THREE.Vector3(Math.cos(a), Math.sin(a), 0).multiplyScalar(RADIUS)
        }),
      ),
      new THREE.LineBasicMaterial({ color: 0x39457f, transparent: true, opacity: 0.6 }),
    )
    world.add(ring)

    // State vector
    const v = new THREE.Vector3(x, y, z).normalize().multiplyScalar(RADIUS * 0.92)
    const arrowGroup = new THREE.Group()
    const shaft = new THREE.Mesh(
      new THREE.CylinderGeometry(0.05, 0.05, v.length(), 12),
      new THREE.MeshBasicMaterial({ color }),
    )
    shaft.position.copy(v.clone().multiplyScalar(0.5))
    shaft.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), v.clone().normalize())
    arrowGroup.add(shaft)
    const head = new THREE.Mesh(
      new THREE.ConeGeometry(0.1, 0.24, 12),
      new THREE.MeshBasicMaterial({ color }),
    )
    head.position.copy(v.clone().multiplyScalar(1.06))
    head.quaternion.copy(shaft.quaternion)
    arrowGroup.add(head)
    world.add(arrowGroup)

    const projDot = new THREE.Mesh(new THREE.SphereGeometry(0.07, 12, 12), new THREE.MeshBasicMaterial({ color: 0xffffff }))
    projDot.position.copy(v)
    world.add(projDot)

    let raf = 0
    const animate = () => {
      world.rotation.y += 0.0025
      world.rotation.x = Math.sin(Date.now() / 6000) * 0.12
      raf = requestAnimationFrame(animate)
      renderer.render(scene, camera)
    }
    animate()

    return () => {
      cancelAnimationFrame(raf)
      renderer.dispose()
      if (renderer.domElement.parentElement === el) el.removeChild(renderer.domElement)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [x, y, z])

  return <div ref={mount} style={{ width: size, height: size }} />
}
