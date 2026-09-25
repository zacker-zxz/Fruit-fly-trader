import React, { useEffect, useRef, useState } from 'react'

/**
 * Interactive Connectome Brain Explorer.
 * Visualizes the fruit fly neural network partitioned by biological compartments:
 * - Optic Lobe (Compound Eyes)
 * - Antennal Lobe (Sensory Olfactory/Turbulence)
 * - Mushroom Body (Kenyon cells & Associative Memory)
 * - Central Complex (Directional Navigation)
 * - Motor Output (Descending Neurons)
 */
export default function BrainExplorer({
  activeNeurons = 0,
  clusters = {},
  neurotransmitters = {},
  events = [],
}) {
  const canvasRef = useRef(null)
  const [selectedCluster, setSelectedCluster] = useState('all')

  const CLUSTERS_META = {
    optic_lobe: { name: 'Optic Lobe (Vision)', color: '#10b981', count: 30, desc: 'Processes price trends & momentum vectors' },
    antennal_lobe: { name: 'Antennal Lobe (Senses)', color: '#f59e0b', count: 25, desc: 'Sensory turbulence & volume shocks' },
    mushroom_body: { name: 'Mushroom Body (Memory)', color: '#8b5cf6', count: 180, desc: 'Associative memory conditioned by dopamine reward' },
    central_complex: { name: 'Central Complex (CX)', color: '#3b82f6', count: 240, desc: 'Steering compass: calculates UP vs DOWN direction' },
    motor_output: { name: 'Descending Motor (VNC)', color: '#ef4444', count: 3, desc: 'Commands thoracic flight muscle: BUY / HOLD / SELL' },
  }

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    let animId

    // Generate cluster coordinates once
    const rng = (s) => {
      let x = Math.sin(s++) * 10000
      return x - Math.floor(x)
    }

    const render = () => {
      const dpr = window.devicePixelRatio || 1
      const w = canvas.clientWidth
      const h = canvas.clientHeight
      if (canvas.width !== w * dpr) {
        canvas.width = w * dpr
        canvas.height = h * dpr
      }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
      ctx.clearRect(0, 0, w, h)

      const cx = w / 2
      const cy = h / 2

      // Draw cluster regions
      const clusterPos = {
        optic_lobe: { x: cx - 180, y: cy - 90, r: 55, color: '#10b981' },
        antennal_lobe: { x: cx - 180, y: cy + 90, r: 50, color: '#f59e0b' },
        mushroom_body: { x: cx, y: cy - 80, r: 75, color: '#8b5cf6' },
        central_complex: { x: cx + 20, y: cy + 60, r: 85, color: '#3b82f6' },
        motor_output: { x: cx + 210, y: cy, r: 40, color: '#ef4444' },
      }

      // 1. Inter-cluster synaptic projection bundles
      ctx.lineWidth = 1.2
      ctx.strokeStyle = 'rgba(148, 163, 184, 0.15)'

      const connectClusters = (c1, c2) => {
        ctx.beginPath()
        ctx.moveTo(c1.x, c1.y)
        ctx.quadraticCurveTo(cx, cy, c2.x, c2.y)
        ctx.stroke()
      }

      connectClusters(clusterPos.optic_lobe, clusterPos.mushroom_body)
      connectClusters(clusterPos.optic_lobe, clusterPos.central_complex)
      connectClusters(clusterPos.antennal_lobe, clusterPos.mushroom_body)
      connectClusters(clusterPos.antennal_lobe, clusterPos.central_complex)
      connectClusters(clusterPos.mushroom_body, clusterPos.central_complex)
      connectClusters(clusterPos.central_complex, clusterPos.motor_output)

      // 2. Draw neurons inside clusters
      let seed = 42
      Object.entries(clusterPos).forEach(([key, cp]) => {
        const isDimmed = selectedCluster !== 'all' && selectedCluster !== key
        const count = CLUSTERS_META[key]?.count || 30
        const activeInCluster = clusters[key] || 0

        // Cluster boundary circle
        ctx.strokeStyle = isDimmed ? 'rgba(51, 65, 85, 0.3)' : cp.color
        ctx.lineWidth = 1.5
        ctx.setLineDash([4, 4])
        ctx.beginPath()
        ctx.arc(cp.x, cp.y, cp.r, 0, Math.PI * 2)
        ctx.stroke()
        ctx.setLineDash([])

        // Cluster title
        ctx.fillStyle = isDimmed ? '#475569' : cp.color
        ctx.font = 'bold 12px Inter, sans-serif'
        ctx.textAlign = 'center'
        ctx.fillText(CLUSTERS_META[key]?.name || key, cp.x, cp.y - cp.r - 8)

        // Cluster active count badge
        ctx.fillStyle = isDimmed ? '#334155' : 'rgba(255, 255, 255, 0.8)'
        ctx.font = '10px Inter, monospace'
        ctx.fillText(`Active: ${activeInCluster} / ${count}`, cp.x, cp.y + cp.r + 14)

        // Neurons inside cluster
        for (let i = 0; i < count; i++) {
          const angle = rng(seed++) * Math.PI * 2
          const dist = Math.sqrt(rng(seed++)) * (cp.r - 10)
          const nx = cp.x + Math.cos(angle) * dist
          const ny = cp.y + Math.sin(angle) * dist

          const isFired = i < activeInCluster
          ctx.beginPath()
          ctx.arc(nx, ny, isFired ? 4 : 2, 0, Math.PI * 2)
          if (isFired) {
            ctx.fillStyle = '#ffffff'
            ctx.shadowColor = cp.color
            ctx.shadowBlur = 8
          } else {
            ctx.fillStyle = isDimmed ? 'rgba(71, 85, 105, 0.4)' : cp.color + '66'
            ctx.shadowBlur = 0
          }
          ctx.fill()
          ctx.shadowBlur = 0
        }
      })
    }

    render()
  }, [clusters, selectedCluster])

  return (
    <div className="brain-explorer-page">
      <div className="explorer-header">
        <div>
          <h2>Fruit Fly Connectome Architecture</h2>
          <p className="subtitle">
            Signal propagation pathways from compound eyes through Mushroom Body to descending motor neurons.
          </p>
        </div>
        <div className="cluster-filter-pills">
          <button
            className={`pill ${selectedCluster === 'all' ? 'active' : ''}`}
            onClick={() => setSelectedCluster('all')}
          >
            All Clusters
          </button>
          {Object.entries(CLUSTERS_META).map(([key, meta]) => (
            <button
              key={key}
              className={`pill ${selectedCluster === key ? 'active' : ''}`}
              style={{ borderColor: selectedCluster === key ? meta.color : undefined }}
              onClick={() => setSelectedCluster(key)}
            >
              {meta.name}
            </button>
          ))}
        </div>
      </div>

      <div className="explorer-canvas-container">
        <canvas ref={canvasRef} className="explorer-canvas" />
      </div>

      {/* Cluster Meta Cards */}
      <div className="clusters-grid">
        {Object.entries(CLUSTERS_META).map(([key, meta]) => (
          <div
            key={key}
            className={`cluster-card ${selectedCluster === key ? 'selected' : ''}`}
            onClick={() => setSelectedCluster(key)}
          >
            <div className="c-card-header">
              <span className="c-dot" style={{ background: meta.color }} />
              <strong style={{ color: meta.color }}>{meta.name}</strong>
            </div>
            <p className="c-desc">{meta.desc}</p>
            <div className="c-footer">
              <span>Current Spikes: <strong>{clusters[key] || 0}</strong></span>
              <span>Total Neurons: <strong>{meta.count}</strong></span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
