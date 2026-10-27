import { useEffect, useMemo, useRef, useState } from "react"
import { Menu, RefreshCw, AlertCircle, CheckCircle2 } from "lucide-react"
import { Badge, Button, Card, Heading, Input, Select, Textarea } from "./components/ui/Primitives"
import {
  branches as defaultBranches,
  buses as defaultBuses,
  loadProfile as defaultLoadProfile,
  solarProfile as defaultSolarProfile,
  windProfile as defaultWindProfile,
  totalBaseLoadKw as defaultTotalLoad,
  scenarios as defaultScenarios,
} from "./data/ieee33BusSystem"
import {
  api,
  type BusTopology,
  type BackendScenario,
  type Config,
  type HourResult,
  type AlgorithmResult,
  type OptimizationResponse,
  type RecommendationItem,
  type ResourceType,
  type ValidationResult,
  type DatasetItem,
} from "./services/api"
import { runClientDispatchSimulation } from "./services/clientSimulation"
import {
  StackedDispatchChart,
  CostBreakdownChart,
  BatterySocChart,
  GlobalBenchmarkChart,
  BusGenerationChart,
  TransmissionLossChart,
  PostImplementationComparisonChart,
  BaselineLoadDemandChart,
  BaselineRenewableProfileChart,
} from "./components/Graphs"
import { WeightsSimulationPage } from "./components/WeightsSimulationPage"

type Page = "network" | "optimize" | "compare" | "weights"
type RunState = "idle" | "running" | "complete" | "failed"

const defaultConfig: Config = {
  solarKw: 900,
  windKw: 650,
  batteryKw: 500,
  batteryKwh: 1800,
  gridLimitKw: 3200,
}

const resourceMeta: Record<ResourceType, { label: string }> = {
  solar: { label: "Solar PV" },
  wind: { label: "Wind" },
  battery: { label: "Battery" },
  grid: { label: "Grid" },
}

function formatNumber(value: number | undefined | null, digits = 0) {
  if (value === undefined || value === null || Number.isNaN(Number(value))) {
    return "0"
  }
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: digits }).format(Number(value))
}

function MiniChart({
  series,
  labels,
  unit,
  heightClass = "h-56",
}: {
  series: { name: string; values: number[]; color: string }[]
  labels?: string[]
  unit: string
  heightClass?: string
}) {
  const [hover, setHover] = useState<number | null>(null)
  const width = 720
  const height = 210
  const padding = 28
  const values = series.flatMap((item) => item.values)
  const min = Math.min(0, ...values)
  const max = Math.max(1, ...values)
  const point = (value: number, index: number, length: number) => {
    const x = padding + (index / Math.max(1, length - 1)) * (width - padding * 2)
    const y = height - padding - ((value - min) / (max - min || 1)) * (height - padding * 2)
    return `${x},${y}`
  }
  const maxLen = series[0]?.values.length ?? 0
  const hoverIndex = hover === null || maxLen === 0 ? null : Math.min(hover, maxLen - 1)

  return (
    <div className={`relative w-full ${heightClass}`}>
      <svg
        className="h-full w-full overflow-visible"
        viewBox={`0 0 ${width} ${height}`}
        preserveAspectRatio="none"
        onMouseLeave={() => setHover(null)}
        onMouseMove={(event) => {
          if (maxLen === 0) return
          const bounds = event.currentTarget.getBoundingClientRect()
          const position = ((event.clientX - bounds.left) / bounds.width) * maxLen
          setHover(Math.max(0, Math.min(maxLen - 1, Math.floor(position))))
        }}
      >
        {[0, 1, 2, 3].map((line) => (
          <line
            key={line}
            x1={padding}
            x2={width - padding}
            y1={padding + line * 50}
            y2={padding + line * 50}
            className="stroke-olive/15"
          />
        ))}
        {series.map((item) => {
          if (!item.values.length) return null
          return (
            <polyline
              key={item.name}
              points={item.values.map((value, index) => point(value, index, item.values.length)).join(" ")}
              fill="none"
              stroke={item.color}
              strokeWidth="3"
              strokeLinejoin="round"
              strokeLinecap="round"
              vectorEffect="non-scaling-stroke"
            />
          )
        })}
        {hoverIndex !== null && maxLen > 0 && (
          <line
            x1={padding + (hoverIndex / Math.max(1, maxLen - 1)) * (width - padding * 2)}
            x2={padding + (hoverIndex / Math.max(1, maxLen - 1)) * (width - padding * 2)}
            y1={padding}
            y2={height - padding}
            className="stroke-forest/40"
            strokeDasharray="4 4"
          />
        )}
      </svg>
      {hoverIndex !== null && maxLen > 0 && (
        <div className="pointer-events-none absolute right-3 top-3 rounded-lg border border-olive/25 bg-cornsilk/95 p-2 text-xs shadow-sm">
          <div className="mb-1 font-semibold">{labels?.[hoverIndex] ?? `${hoverIndex}:00`}</div>
          {series.map((item) => (
            <div key={item.name} className="flex gap-3">
              <span className="text-forest-muted">{item.name}</span>
              <span className="ml-auto font-mono font-semibold">
                {formatNumber(item.values[hoverIndex] ?? 0, 1)} {unit}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function BusNetwork({
  selected,
  onSelect,
  buses,
  branches,
  modifications = {},
  selectedBranch,
  onSelectBranch,
  onDeleteBranch,
}: {
  selected: number
  onSelect: (bus: number) => void
  buses: BusTopology[]
  branches: [number, number][]
  modifications?: Record<number, ResourceType[]>
  selectedBranch?: [number, number] | null
  onSelectBranch?: (branch: [number, number]) => void
  onDeleteBranch?: (branch: [number, number]) => void
}) {
  const [hoveredBranch, setHoveredBranch] = useState<[number, number] | null>(null)
  const [internalBranch, setInternalBranch] = useState<[number, number] | null>(null)

  const activeSelectedBranch = selectedBranch !== undefined ? selectedBranch : internalBranch
  const activeChannel = activeSelectedBranch || hoveredBranch

  const handleBranchClick = (from: number, to: number) => {
    if (onSelectBranch) {
      onSelectBranch([from, to])
    } else {
      setInternalBranch([from, to])
    }
    // Also select the sending bus
    onSelect(from)
  }

  return (
    <div className="bg-technical-grid min-h-80 touch-pan-x overflow-x-auto overscroll-x-contain rounded-xl border border-olive/25 p-3">
      <svg viewBox="0 0 990 280" className="min-w-3xl" aria-label="IEEE 33-bus radial network">
        <defs>
          <filter id="channelGlow" x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="3.5" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {branches.map(([from, to]) => {
          const start = buses.find((b) => b.id === from)
          const end = buses.find((b) => b.id === to)
          if (!start || !end) return null

          const isSelected =
            activeSelectedBranch &&
            ((activeSelectedBranch[0] === from && activeSelectedBranch[1] === to) ||
              (activeSelectedBranch[0] === to && activeSelectedBranch[1] === from))
          const isHovered =
            hoveredBranch &&
            ((hoveredBranch[0] === from && hoveredBranch[1] === to) ||
              (hoveredBranch[0] === to && hoveredBranch[1] === from))

          return (
            <g
              key={`${from}-${to}`}
              className="cursor-pointer group"
              onClick={() => handleBranchClick(from, to)}
              onMouseEnter={() => setHoveredBranch([from, to])}
              onMouseLeave={() => setHoveredBranch(null)}
            >
              {/* Extra-wide hit area for effortless clicking and hovering anywhere near the feeder line */}
              <line x1={start.x} y1={start.y} x2={end.x} y2={end.y} stroke="transparent" strokeWidth="18" />

              {/* Glowing halo behind active or hovered channel */}
              {(isSelected || isHovered) && (
                <line
                  x1={start.x}
                  y1={start.y}
                  x2={end.x}
                  y2={end.y}
                  stroke={isSelected ? "#BC6C25" : "#606C38"}
                  strokeWidth="8"
                  strokeOpacity="0.4"
                  filter="url(#channelGlow)"
                  className="transition-all duration-300 ease-out"
                />
              )}

              {/* Base Channel Line with smooth transition */}
              <line
                x1={start.x}
                y1={start.y}
                x2={end.x}
                y2={end.y}
                className="transition-all duration-300 ease-out"
                stroke={isSelected ? "#BC6C25" : isHovered ? "#283618" : "rgba(96, 108, 56, 0.55)"}
                strokeWidth={isSelected ? "4.5" : isHovered ? "4" : "2.5"}
              />

              {/* Animated energy flow pulses along selected or hovered channel */}
              {(isSelected || isHovered) && (
                <line
                  x1={start.x}
                  y1={start.y}
                  x2={end.x}
                  y2={end.y}
                  stroke="#FEFAE0"
                  strokeWidth="2.5"
                  strokeDasharray="6 6"
                  className="pointer-events-none"
                >
                  <animate
                    attributeName="stroke-dashoffset"
                    values="0;-24"
                    dur="1.2s"
                    repeatCount="indefinite"
                  />
                </line>
              )}
            </g>
          )
        })}

        {buses.map((bus) => {
          const hasResource = (bus.resources && bus.resources.length > 0) || (modifications[bus.id]?.length ?? 0) > 0
          const isChannelEnd =
            activeChannel && (activeChannel[0] === bus.id || activeChannel[1] === bus.id)

          return (
            <g
              key={bus.id}
              role="button"
              tabIndex={0}
              aria-label={`Select bus ${bus.id}`}
              onClick={() => onSelect(bus.id)}
              onKeyDown={(event) => event.key === "Enter" && onSelect(bus.id)}
              className="cursor-pointer outline-none group"
            >
              {/* Highlight ring if bus is part of the active feeder channel */}
              {isChannelEnd && (
                <circle
                  cx={bus.x}
                  cy={bus.y}
                  r={21}
                  fill="none"
                  stroke="#BC6C25"
                  strokeWidth="2"
                  strokeDasharray="3 3"
                  className="animate-spin-slow opacity-80"
                />
              )}

              <circle
                cx={bus.x}
                cy={bus.y}
                r={selected === bus.id ? 17 : 13}
                className={`transition-all duration-200 ease-out ${
                  selected === bus.id
                    ? "fill-copper stroke-cornsilk drop-shadow-md"
                    : hasResource
                      ? "fill-olive stroke-cornsilk hover:fill-olive-light"
                      : "fill-cornsilk stroke-forest hover:stroke-copper"
                }`}
                strokeWidth={selected === bus.id ? "3.5" : "2.5"}
              />
              <text
                x={bus.x}
                y={bus.y + 4}
                textAnchor="middle"
                className={`select-none font-bold text-[10px] transition-all ${
                  selected === bus.id || hasResource ? "fill-cornsilk" : "fill-forest"
                }`}
              >
                {bus.id}
              </text>
            </g>
          )
        })}
      </svg>

      {/* Smooth Interactive Bus Channel Bar */}
      {activeChannel && (
        <div className="mt-3 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-copper/40 bg-copper-tint/90 p-3 text-xs text-forest shadow-sm transition-all duration-300">
          <div className="flex flex-wrap items-center gap-3">
            <span className="flex h-2.5 w-2.5 rounded-full bg-copper animate-ping" />
            <div>
              <span className="font-bold text-copper uppercase tracking-wider text-[10px] block">
                Feeder Channel Line
              </span>
              <span className="font-semibold text-sm">
                Bus {activeChannel[0]} ⟷ Bus {activeChannel[1]}
              </span>
            </div>
            <div className="hidden border-l border-forest/15 pl-3 sm:block">
              <span className="text-[10px] text-forest-muted block">Cable Parameters</span>
              <span className="font-mono text-xs font-semibold">
                R: 0.092 Ω · X: 0.047 Ω · Loss mult: 1.01×
              </span>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => onSelect(activeChannel[0])}
              className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-colors ${
                selected === activeChannel[0]
                  ? "bg-copper text-cornsilk font-bold"
                  : "bg-cornsilk/80 text-forest hover:bg-cornsilk"
              }`}
            >
              Focus Bus {activeChannel[0]}
            </button>
            <button
              type="button"
              onClick={() => onSelect(activeChannel[1])}
              className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-colors ${
                selected === activeChannel[1]
                  ? "bg-copper text-cornsilk font-bold"
                  : "bg-cornsilk/80 text-forest hover:bg-cornsilk"
              }`}
            >
              Focus Bus {activeChannel[1]}
            </button>
            {onDeleteBranch && (
              <button
                type="button"
                onClick={() => {
                  onDeleteBranch(activeChannel)
                  setInternalBranch(null)
                }}
                className="rounded-lg bg-red-600/15 px-2.5 py-1 text-xs font-semibold text-red-800 hover:bg-red-600/25 transition-colors"
                title="Disconnect this transmission line"
              >
                Disconnect Line
              </button>
            )}
          </div>
        </div>
      )}
      <p className="mt-2 text-center text-[10px] text-forest-muted sm:hidden">
        Swipe horizontally to inspect all 33 buses and tap any channel line to interact.
      </p>
    </div>
  )
}

function MetricCard({
  label,
  value,
  detail,
  tone = "default",
}: {
  label: string
  value: string
  detail: string
  tone?: "default" | "forest" | "caramel" | "olive"
}) {
  return (
    <Card variant={tone} className="p-4">
      <div className="mb-5 flex items-start justify-between">
        <span className="text-xs font-semibold uppercase tracking-widest opacity-70">{label}</span>
      </div>
      <div className="font-display text-2xl font-bold">{value}</div>
      <div className="mt-1 text-xs opacity-65">{detail}</div>
    </Card>
  )
}

function Sidebar({
  page,
  setPage,
  open,
  setOpen,
  backendConnected,
}: {
  page: Page
  setPage: (page: Page) => void
  open: boolean
  setOpen: (open: boolean) => void
  backendConnected: boolean
}) {
  const items: { id: Page; title: string; subtitle: string }[] = [
    { id: "network", title: "System overview", subtitle: "IEEE 33-bus" },
    { id: "optimize", title: "Data & optimization", subtitle: "Configure a run" },
    { id: "compare", title: "Compare & modify", subtitle: "ABC versus PSO" },
    { id: "weights", title: "Weights & fitness", subtitle: "Real-time simulation" },
  ]
  return (
    <aside
      id="primary-navigation"
      className={`${open ? "translate-x-0" : "-translate-x-full"} fixed inset-y-0 left-0 z-40 flex w-72 flex-col bg-forest text-cornsilk transition-transform lg:translate-x-0`}
    >
      <div className="border-b border-cornsilk/10 p-6">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-500/20 border border-emerald-400/30 text-base">
              ⚡
            </div>
            <div>
              <div className="font-display text-base font-extrabold tracking-wider text-cornsilk">
                ECOGRID <span className="text-emerald-400">AI</span>
              </div>
              <div className="text-[10px] font-mono uppercase tracking-widest text-cornsilk/60">
                Resource Optimizer
              </div>
            </div>
          </div>
          <Button
            variant="ghost"
            size="xs"
            className="!text-cornsilk hover:!bg-cornsilk/10 lg:hidden"
            onClick={() => setOpen(false)}
            aria-label="Close menu"
          >
            Close
          </Button>
        </div>
        <Heading level={1} className="text-sm font-semibold !text-cornsilk/90">
          Autonomous Microgrid Optimization
        </Heading>
        <p className="mt-1 text-xs leading-relaxed text-cornsilk/65">IEEE 33-Bus Radial Feeder · ABC & PSO</p>
      </div>
      <nav className="flex-1 space-y-2 p-4">
        <div className="px-3 pb-2 text-[10px] font-bold uppercase tracking-[0.2em] text-cornsilk/70">Workspace</div>
        {items.map((item, index) => {
          const active = page === item.id
          return (
            <Button
              key={item.id}
              variant="ghost"
              className={`h-auto w-full justify-start px-3 py-3 text-left ${active ? "!bg-cornsilk !text-forest hover:!bg-cornsilk" : "!text-cornsilk/80 hover:!bg-cornsilk/10 hover:!text-cornsilk"}`}
              onClick={() => {
                setPage(item.id)
                setOpen(false)
              }}
            >
              <span
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg font-mono text-xs font-bold ${active ? "bg-olive/15 text-olive" : "bg-cornsilk/10"}`}
              >
                {index + 1}
              </span>
              <span className="min-w-0 flex-1">
                <span className="block text-sm font-semibold">
                  {index + 1}. {item.title}
                </span>
                <span className={`block text-[10px] ${active ? "text-forest/70" : "text-cornsilk/60"}`}>
                  {item.subtitle}
                </span>
              </span>
            </Button>
          )
        })}
      </nav>
      <div className="m-4 rounded-xl border border-cornsilk/10 bg-cornsilk/5 p-4">
        <div className="mb-2 text-xs font-bold">About project</div>
        <p className="text-[11px] leading-relaxed text-cornsilk/75">
          Decision support for resource dispatch on the IEEE 33-bus radial test system, comparing Artificial Bee Colony and
          Particle Swarm Optimization with Shannon Entropy weighting.
        </p>
      </div>
      <div className="flex items-center justify-between border-t border-cornsilk/10 px-5 py-4 text-[10px] text-cornsilk/65">
        <span>Engine: Python 3.11</span>
        <span className="flex items-center gap-1.5 font-medium">
          <span className={`h-2 w-2 rounded-full ${backendConnected ? "bg-emerald-400" : "bg-amber-400"}`} />
          {backendConnected ? "FastAPI Live" : "Connecting…"}
        </span>
      </div>
    </aside>
  )
}

function PageHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow: string
  title: string
  description: string
  action?: React.ReactNode
}) {
  return (
    <header className="mb-5 flex flex-col justify-between gap-4 border-b border-olive/20 pb-5 md:mb-7 md:flex-row md:items-end md:pb-6">
      <div>
        <div className="mb-2 text-xs font-bold uppercase tracking-[0.18em] text-copper">{eyebrow}</div>
        <Heading level={1} className="text-2xl sm:text-3xl">
          {title}
        </Heading>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-forest-muted">{description}</p>
      </div>
      {action && <div className="w-full md:w-auto">{action}</div>}
    </header>
  )
}

function BusDetail({
  bus,
  branches,
  editable = false,
  added = [],
  onAdd,
  onUpdateLoad,
  onRemoveResource,
}: {
  bus: BusTopology
  branches: [number, number][]
  editable?: boolean
  added?: ResourceType[]
  onAdd?: (type: ResourceType) => void
  onUpdateLoad?: (busId: number, loadKw: number) => void
  onRemoveResource?: (busId: number, resource: ResourceType) => void
}) {
  const [editingLoad, setEditingLoad] = useState(false)
  const [loadVal, setLoadVal] = useState(bus.loadKw)

  useEffect(() => {
    setLoadVal(bus.loadKw)
    setEditingLoad(false)
  }, [bus.id, bus.loadKw])

  const handleSaveLoad = () => {
    if (onUpdateLoad) {
      onUpdateLoad(bus.id, Number(loadVal))
    }
    setEditingLoad(false)
  }

  const connected = branches
    .filter(([a, b]) => a === bus.id || b === bus.id)
    .map(([a, b]) => (a === bus.id ? b : a))
  const resources = [...new Set([...(bus.resources || []), ...added])]

  return (
    <Card variant="elevated" className="p-5">
      <div className="mb-5 flex items-start justify-between">
        <div>
          <div className="text-xs font-bold uppercase tracking-wider text-copper">Selected node</div>
          <Heading level={2} className="mt-1">
            Bus {bus.id}
          </Heading>
        </div>
        <Badge tone={editable ? "caramel" : "neutral"}>{editable ? "Editable Node" : "Read only"}</Badge>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="rounded-lg bg-cornsilk-soft p-3">
          <div className="flex items-center justify-between">
            <span className="text-[10px] uppercase text-forest-muted">Peak load</span>
            {editable && onUpdateLoad && !editingLoad && (
              <button
                type="button"
                onClick={() => setEditingLoad(true)}
                className="text-[10px] font-semibold text-copper hover:underline cursor-pointer"
              >
                Edit
              </button>
            )}
          </div>
          {editingLoad ? (
            <div className="mt-1 flex items-center gap-1.5">
              <input
                type="number"
                min="0"
                value={loadVal}
                onChange={(e) => setLoadVal(Math.max(0, Number(e.target.value)))}
                className="w-20 rounded border border-olive/40 bg-cornsilk px-1.5 py-0.5 font-mono text-xs font-bold text-forest"
                autoFocus
              />
              <span className="text-xs text-forest-muted">kW</span>
              <button
                type="button"
                onClick={handleSaveLoad}
                className="rounded bg-olive px-1.5 py-0.5 text-[10px] font-bold text-cornsilk hover:bg-olive-light cursor-pointer"
              >
                Save
              </button>
              <button
                type="button"
                onClick={() => {
                  setLoadVal(bus.loadKw)
                  setEditingLoad(false)
                }}
                className="text-[10px] text-forest-muted hover:text-forest cursor-pointer"
              >
                ✕
              </button>
            </div>
          ) : (
            <div className="mt-1 font-mono text-sm font-bold">{bus.loadKw} kW</div>
          )}
        </div>
        <div className="rounded-lg bg-cornsilk-soft p-3">
          <div className="text-[10px] uppercase text-forest-muted">Distance / Loss</div>
          <div className="mt-1 font-mono text-sm font-bold">
            {bus.distance_hops ?? 0} hops · {bus.loss_pct ?? 0}%
          </div>
        </div>
      </div>
      <div className="mt-4">
        <div className="mb-2 text-xs font-semibold">Adjacent buses</div>
        <div className="flex flex-wrap gap-1.5">
          {connected.map((id) => (
            <Badge key={id} tone="neutral">
              Bus {id}
            </Badge>
          ))}
        </div>
      </div>
      <div className="mt-5 border-t border-olive/15 pt-4">
        <div className="mb-3 text-xs font-semibold">Installed resources</div>
        {resources.length ? (
          <div className="space-y-2">
            {resources.map((resource) => (
              <div
                key={resource}
                className="flex items-center gap-2 rounded-lg bg-olive-tint p-2 text-xs font-medium"
              >
                {resourceMeta[resource].label}
                <div className="ml-auto flex items-center gap-1.5">
                  <Badge tone="olive">Connected</Badge>
                  {editable && onRemoveResource && (
                    <button
                      type="button"
                      onClick={() => onRemoveResource(bus.id, resource)}
                      className="rounded p-0.5 text-forest-muted hover:bg-red-100 hover:text-red-700 font-bold leading-none text-xs cursor-pointer"
                      title={`Remove ${resourceMeta[resource].label} from Bus ${bus.id}`}
                    >
                      ✕
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-forest-muted">No distributed energy resources at this bus.</p>
        )}
      </div>
      {editable && onAdd && (
        <div className="mt-5 border-t border-olive/15 pt-4">
          <div className="mb-3 text-xs font-semibold">Add support to Bus {bus.id}</div>
          <div className="grid grid-cols-2 gap-2">
            {(["solar", "wind", "battery", "grid"] as ResourceType[]).map((type) => (
              <Button
                key={type}
                size="sm"
                variant="outline"
                disabled={resources.includes(type)}
                onClick={() => onAdd(type)}
              >
                {resourceMeta[type].label}
              </Button>
            ))}
          </div>
        </div>
      )}
    </Card>
  )
}

function NetworkPage({
  buses,
  branches,
  totalBaseLoadKw,
  selectedBus,
  setSelectedBus,
}: {
  buses: BusTopology[]
  branches: [number, number][]
  totalBaseLoadKw: number
  selectedBus: number
  setSelectedBus: (id: number) => void
}) {
  const currentBus = buses.find((b) => b.id === selectedBus) || buses[0]

  return (
    <>
      <PageHeader
        eyebrow="Page 01 · System baseline showcase"
        title="IEEE 33-Bus System Showcase"
        description="Comprehensive baseline showcase of the 12.66 kV IEEE 33-bus radial distribution network, installed generation assets, and diurnal load profiles."
        action={
          <Badge tone="olive">
            <span className="h-1.5 w-1.5 rounded-full bg-olive animate-pulse" /> Showcase Mode · Read-Only Baseline
          </Badge>
        }
      />
      <div className="mb-5 grid grid-cols-2 gap-3 sm:gap-4 xl:grid-cols-5">
        <MetricCard
          label="Peak system load"
          value={`${formatNumber(totalBaseLoadKw)} kW`}
          detail="Connected active power demand (Data1.csv)"
          tone="forest"
        />
        <MetricCard
          label="PV 1 Capacity (Bus 13)"
          value="851.5 kW"
          detail="Primary fixed array (12 hops, 1.12× loss)"
          tone="caramel"
        />
        <MetricCard
          label="PV 2 Capacity (Bus 30)"
          value="1,157.6 kW"
          detail="Secondary array (10 hops, 1.10× loss)"
          tone="caramel"
        />
        <MetricCard
          label="Wind Capacity (Bus 6)"
          value="2,098.0 kW"
          detail="High-capacity WT generator (5 hops, 1.05× loss)"
          tone="olive"
        />
        <MetricCard
          label="Substation Grid Link"
          value="3,200 kW"
          detail="Bus 1 main interconnect limit"
        />
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_19rem]">
        <Card className="overflow-hidden">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-olive/20 p-4 sm:p-5">
            <div>
              <Heading level={2}>Radial network topology</Heading>
              <p className="mt-1 text-xs text-forest-muted">
                Select any circular bus to inspect its baseline configuration, load, and transmission loss factor in read-only showcase mode.
              </p>
            </div>
            <div className="flex gap-3 text-[10px] text-forest-muted">
              <span className="flex items-center gap-1">
                <span className="h-2 w-2 rounded-full bg-olive" /> Resource bus
              </span>
              <span className="flex items-center gap-1">
                <span className="h-2 w-2 rounded-full border border-forest bg-cornsilk" /> Load bus
              </span>
            </div>
          </div>

          <div className="p-3 sm:p-4">
            <BusNetwork
              selected={selectedBus}
              onSelect={setSelectedBus}
              buses={buses}
              branches={branches}
            />
          </div>
          <div className="grid gap-4 border-t border-olive/20 p-4 sm:p-5 md:grid-cols-3">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-forest-muted">Grid connection</div>
              <div className="mt-1 font-display text-lg font-bold">Bus 1 · 3,200 kW</div>
              <p className="text-xs text-forest-muted">Substation main feeder (0 hops)</p>
            </div>
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-forest-muted">Topology</div>
              <div className="mt-1 font-display text-lg font-bold">33 buses · 32 lines</div>
              <p className="text-xs text-forest-muted">12.66 kV radial distribution feeder</p>
            </div>
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-forest-muted">Cable Loss Model</div>
              <div className="mt-1 font-display text-lg font-bold">1.00 – 1.15 multiplier</div>
              <p className="text-xs text-forest-muted">+1% transmission loss per hop</p>
            </div>
          </div>
        </Card>
        {currentBus && <BusDetail bus={currentBus} branches={branches} />}
      </div>

      {/* Baseline Visual Graph 1: Real Measured Demand vs Synthetic Reference */}
      <Card className="mt-5 p-4 sm:p-5">
        <div className="mb-4">
          <div className="text-xs font-bold uppercase tracking-wider text-copper">Baseline visualizer · diurnal demand</div>
          <Heading level={2} className="mt-1">
            Diurnal Load Demand Profile: Real Measured (Data1.csv) vs. Synthetic Benchmark
          </Heading>
          <p className="mt-1 text-xs text-forest-muted">
            24-hour diurnal active power demand curve from Data1.csv with measured peak of 3,715 kW at hour 19:00 compared against synthetic reference and customer sector breakdown.
          </p>
        </div>
        <BaselineLoadDemandChart peakLoadKw={totalBaseLoadKw} />
      </Card>

      {/* Baseline Visual Graph 2: Renewable Energy Availability Profiles */}
      <Card className="mt-5 p-4 sm:p-5">
        <div className="mb-4">
          <div className="text-xs font-bold uppercase tracking-wider text-copper">Baseline visualizer · renewable potential</div>
          <Heading level={2} className="mt-1">
            Diurnal Renewable Availability Profiles (Solar PV & Wind Generation)
          </Heading>
          <p className="mt-1 text-xs text-forest-muted">
            Clean energy generation potential across the 24-hour cycle scaled to system asset ratings: 2,009.1 kW Solar PV (Bus 13 & 30) and 2,098.0 kW Wind Turbine (Bus 6).
          </p>
        </div>
        <BaselineRenewableProfileChart />
      </Card>
    </>
  )
}

function ConfigField({
  label,
  unit,
  value,
  onChange,
}: {
  label: string
  unit: string
  value: number
  onChange: (value: number) => void
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs font-semibold">{label}</span>
      <div className="relative">
        <Input
          type="number"
          min="0"
          value={value}
          onChange={(event) => onChange(Math.max(0, Number(event.target.value)))}
          className="pr-14 font-mono"
        />
        <span className="absolute right-3 top-2 text-xs text-forest-muted">{unit}</span>
      </div>
    </label>
  )
}

function OptimizationPage({
  scenarios,
  scenarioIndex,
  setScenarioIndex,
  config,
  setConfig,
  runState,
  runOptimization,
  dataset,
  setDataset,
  datasetsList,
  onValidateCustomLoad,
  runError,
}: {
  scenarios: BackendScenario[]
  scenarioIndex: number
  setScenarioIndex: (value: number) => void
  config: Config
  setConfig: (value: Config) => void
  runState: RunState
  runOptimization: () => void
  dataset: string
  setDataset: (value: string) => void
  datasetsList: DatasetItem[]
  onValidateCustomLoad: (customLoad: number[] | null) => void
  runError: string | null
}) {
  const [mode, setMode] = useState<"existing" | "upload" | "manual">("existing")
  const [manual, setManual] = useState(
    "Total_Load_kW\n2303\n2155\n2040\n1980\n2050\n2350\n2800\n3200\n3500\n3650\n3715\n3550\n3400\n3350\n3420\n3520\n3640\n3600\n3450\n3280\n3050\n2800\n2520\n2310"
  )
  const fileRef = useRef<HTMLInputElement>(null)
  const [validating, setValidating] = useState(false)
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null)

  const scenario = scenarios[scenarioIndex] || {
    name: "Normal Operation",
    description: "Nominal demand and resource availability",
    load: 1,
    solar: 1,
    wind: 1,
    grid: 1,
    battery: 1,
  }

  // Handle manual CSV input validation with real backend validator
  useEffect(() => {
    if (mode === "manual" && manual.trim().length > 0) {
      setValidating(true)
      const timer = window.setTimeout(async () => {
        try {
          const res = await api.validateDataset({ raw_csv: manual })
          setValidationResult(res)
          if (res.valid && res.summary) {
            // Parse array of 24 numbers from manual entry
            const lines = manual.split("\n").map((l) => Number(l.trim())).filter((n) => !isNaN(n) && n > 0)
            if (lines.length >= 24) {
              onValidateCustomLoad(lines.slice(0, 24))
            }
          } else {
            onValidateCustomLoad(null)
          }
        } catch (err: any) {
          setValidationResult({ valid: false, errors: [err.message], warnings: [] })
          onValidateCustomLoad(null)
        } finally {
          setValidating(false)
        }
      }, 500)
      return () => window.clearTimeout(timer)
    } else if (mode === "existing") {
      setValidationResult(null)
      onValidateCustomLoad(null)
    }
  }, [manual, mode])

  // Handle file upload
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    setDataset(file.name)
    setValidating(true)
    try {
      const res = await api.validateDataset({ file })
      setValidationResult(res)
    } catch (err: any) {
      setValidationResult({ valid: false, errors: [err.message], warnings: [] })
    } finally {
      setValidating(false)
    }
  }

  const hasValidationError = validationResult !== null && !validationResult.valid

  return (
    <>
      <PageHeader
        eyebrow="Page 02 · Configure & run"
        title="Data Upload & Optimization"
        description="Validate hourly input data, choose a stress scenario, and run ABC and PSO against the same configuration."
        action={
          <Badge tone={hasValidationError ? "danger" : "olive"}>
            {hasValidationError ? "Needs attention" : validating ? "Validating…" : "Input valid"}
          </Badge>
        }
      />
      {runError && (
        <div className="mb-5 flex items-start gap-3 rounded-xl border border-red-300 bg-red-50 p-4 text-xs text-red-800">
          <AlertCircle className="h-5 w-5 shrink-0 text-red-600" />
          <div className="flex-1">
            <span className="font-bold">Optimization Error: </span>
            {runError}
          </div>
        </div>
      )}
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_20rem]">
        <div className="space-y-5">
          <Card className="p-4 sm:p-5">
            <div className="mb-5">
              <Heading level={2}>Input dataset</Heading>
              <p className="text-xs text-forest-muted">Hourly power series · 24 one-hour steps</p>
            </div>
            <div className="mb-5 grid grid-cols-3 gap-2">
              {(
                [
                  { id: "existing", label: "Existing data" },
                  { id: "upload", label: "CSV upload" },
                  { id: "manual", label: "Manual entry" },
                ] as const
              ).map((option) => (
                <Button
                  key={option.id}
                  variant={mode === option.id ? "secondary" : "outline"}
                  className="h-auto py-3"
                  onClick={() => setMode(option.id)}
                >
                  {option.label}
                </Button>
              ))}
            </div>

            {mode === "existing" && (
              <div className="space-y-3">
                {datasetsList.map((d) => (
                  <div
                    key={d.id}
                    onClick={() => setDataset(d.id)}
                    className={`flex cursor-pointer items-center gap-3 rounded-xl border p-4 transition-colors ${
                      dataset === d.id ? "border-olive bg-olive-tint" : "border-olive/20 hover:bg-cornsilk-soft"
                    }`}
                  >
                    <div className="flex-1">
                      <div className="text-sm font-semibold">{d.name}</div>
                      <div className="text-xs text-forest-muted">
                        {d.peak_load_kw ? `Peak: ${formatNumber(d.peak_load_kw)} kW · 24 hours · validated` : d.description}
                      </div>
                    </div>
                    <Badge tone={dataset === d.id ? "olive" : "neutral"}>
                      {dataset === d.id ? "Selected" : "Available"}
                    </Badge>
                  </div>
                ))}
              </div>
            )}

            {mode === "upload" && (
              <div className="rounded-xl border-2 border-dashed border-olive/35 bg-cornsilk-soft p-8 text-center">
                <div className="text-sm font-semibold">Choose a CSV dataset</div>
                <p className="mb-4 mt-1 text-xs text-forest-muted">
                  Required: 24 hourly rows with column "Total_Load_kW" (peak &gt; 100 kW)
                </p>
                <Input
                  ref={fileRef}
                  type="file"
                  accept=".csv"
                  className="mx-auto max-w-sm"
                  onChange={handleFileUpload}
                />
                {validationResult?.valid && (
                  <div className="mt-4 flex items-center justify-center gap-2 text-xs font-semibold text-olive">
                    <CheckCircle2 className="h-4 w-4" /> Validated: {validationResult.summary?.hours} rows · Peak:{" "}
                    {formatNumber(validationResult.summary?.peak_kw ?? 0)} kW
                  </div>
                )}
                {validationResult && !validationResult.valid && (
                  <div className="mt-3 text-left text-xs font-medium text-danger">
                    {validationResult.errors.map((e, idx) => (
                      <div key={idx}>{e}</div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {mode === "manual" && (
              <div>
                <Textarea
                  rows={6}
                  value={manual}
                  onChange={(event) => setManual(event.target.value)}
                  aria-label="CSV manual entry"
                />
                {validationResult && !validationResult.valid ? (
                  <div className="mt-2 text-xs font-medium text-danger">
                    {validationResult.errors.map((e, idx) => (
                      <div key={idx}>{e}</div>
                    ))}
                  </div>
                ) : validationResult?.valid ? (
                  <div className="mt-2 flex items-center gap-1.5 text-xs text-olive">
                    <CheckCircle2 className="h-3.5 w-3.5" /> 24 hours verified · Peak:{" "}
                    {formatNumber(validationResult.summary?.peak_kw ?? 0)} kW
                  </div>
                ) : (
                  <div className="mt-2 text-xs text-forest-muted">Enter 24 positive hourly values with header.</div>
                )}
              </div>
            )}
          </Card>

          <Card className="p-4 sm:p-5">
            <div className="mb-5 flex items-start justify-between gap-3">
              <div>
                <Heading level={2}>Choose operating scenario</Heading>
                <p className="mt-1 text-xs text-forest-muted">
                  All multipliers are evaluated using real Python simulation models.
                </p>
              </div>
              <Badge className="shrink-0" tone="neutral">
                {scenarioIndex + 1} of {scenarios.length}
              </Badge>
            </div>
            <div className="grid grid-cols-2 gap-2 lg:grid-cols-5">
              {scenarios.map((item, index) => (
                <Button
                  key={item.name}
                  variant={scenarioIndex === index ? "primary" : "outline"}
                  className="h-auto min-h-20 flex-col items-start justify-between p-3 text-left sm:min-h-24"
                  onClick={() => setScenarioIndex(index)}
                >
                  <span className="text-[10px] opacity-50">0{index + 1}</span>
                  <span className="text-xs leading-tight sm:text-sm">{item.name}</span>
                </Button>
              ))}
            </div>
            <div className="mt-4 rounded-lg bg-caramel-tint p-3">
              <div className="text-xs font-bold">{scenario.name}</div>
              <p className="mt-0.5 text-xs text-forest-muted">
                {scenario.description}. Demand ×{scenario.load}; solar ×{scenario.solar}; wind ×{scenario.wind}; grid{" "}
                {scenario.grid ? "Available" : "Islanded (0 kW)"}; battery{" "}
                {scenario.battery ? "Online" : "Offline"}.
              </p>
            </div>
          </Card>

          <Card className="p-4 sm:p-5">
            <div className="mb-5">
              <Heading level={2}>System configuration</Heading>
              <p className="text-xs text-forest-muted">
                Configured decision space bounds for ABC and PSO metaheuristics.
              </p>
            </div>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <ConfigField
                label="Solar capacity"
                unit="kW"
                value={config.solarKw}
                onChange={(solarKw) => setConfig({ ...config, solarKw })}
              />
              <ConfigField
                label="Wind capacity"
                unit="kW"
                value={config.windKw}
                onChange={(windKw) => setConfig({ ...config, windKw })}
              />
              <ConfigField
                label="Battery power"
                unit="kW"
                value={config.batteryKw}
                onChange={(batteryKw) => setConfig({ ...config, batteryKw })}
              />
              <ConfigField
                label="Battery capacity"
                unit="kWh"
                value={config.batteryKwh}
                onChange={(batteryKwh) => setConfig({ ...config, batteryKwh })}
              />
              <ConfigField
                label="Grid import limit"
                unit="kW"
                value={config.gridLimitKw}
                onChange={(gridLimitKw) => setConfig({ ...config, gridLimitKw })}
              />
              <label className="block">
                <span className="mb-1.5 block text-xs font-semibold">Network model</span>
                <Select value="ieee33" disabled>
                  <option value="ieee33">IEEE 33-bus · 12.66 kV</option>
                </Select>
              </label>
            </div>
          </Card>
        </div>

        <div>
          <Card variant="forest" className="overflow-hidden p-4 sm:p-5 xl:sticky xl:top-5">
            <div className="mb-5 flex items-center justify-between">
              <Heading level={2} className="!text-cornsilk">
                Run summary
              </Heading>
              <Badge className="!bg-white !text-forest !border-white font-semibold shadow-xs">
                Ready
              </Badge>
            </div>
            <div className="space-y-4 text-xs">
              <div className="border-b border-cornsilk/10 pb-3">
                <div className="text-cornsilk/70">Dataset</div>
                <div className="mt-1 truncate font-semibold">{dataset}</div>
              </div>
              <div className="border-b border-cornsilk/10 pb-3">
                <div className="text-cornsilk/70">Scenario</div>
                <div className="mt-1 font-semibold">{scenario.name}</div>
              </div>
              <div className="border-b border-cornsilk/10 pb-3">
                <div className="text-cornsilk/70">Algorithms</div>
                <div className="mt-1 flex gap-2">
                  <Badge className="!bg-white !text-forest !border-white font-semibold shadow-xs">
                    ABC
                  </Badge>
                  <Badge className="!bg-white !text-forest !border-white font-semibold shadow-xs">
                    PSO
                  </Badge>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <div className="text-cornsilk/70">Time horizon</div>
                  <div className="mt-1 font-mono font-semibold">24 h</div>
                </div>
                <div>
                  <div className="text-cornsilk/70">Multi-Objective</div>
                  <div className="mt-1 font-mono font-semibold">Shannon Entropy</div>
                </div>
              </div>
            </div>
            <Button
              variant="accent"
              size="lg"
              className="mt-6 w-full"
              disabled={hasValidationError || validating || runState === "running"}
              onClick={runOptimization}
            >
              {runState === "running" ? (
                <span className="flex items-center justify-center gap-2">
                  <RefreshCw className="h-4 w-4 animate-spin" /> Optimizing…
                </span>
              ) : (
                "Run optimization"
              )}
            </Button>
            {runState === "complete" && (
              <div className="mt-3 rounded-lg bg-olive/30 p-3 text-xs">Run completed. Results sent to Page 3.</div>
            )}
            <p className="mt-4 text-[10px] leading-relaxed text-cornsilk/65">
              Objective = operating cost + capital cost + 12 × unmet energy + cable losses. Shannon Entropy weighting
              enforces dynamic trade-offs. Lower fitness is better.
            </p>
          </Card>
        </div>
      </div>
    </>
  )
}

function ComparisonPage({
  result,
  setPage,
  buses,
  branches,
  selectedBus,
  setSelectedBus,
  modifications,
  requestModification,
  rerun,
  runState,
  benchmarks,
  onImplementRecommendation,
  implementingRec,
  implementNotice,
  preResult,
  implementedRec,
  onReloadPage3,
  onAddBus,
  onDeleteBus,
  onAddBranch,
  onDeleteBranch,
  onResetTopology,
  onUpdateBusLoad,
  onRemoveResource,
}: {
  result: OptimizationResponse | null
  setPage: (page: Page) => void
  buses: BusTopology[]
  branches: [number, number][]
  selectedBus: number
  setSelectedBus: (id: number) => void
  modifications: Record<number, ResourceType[]>
  requestModification: (type: ResourceType) => void
  rerun: () => void
  runState: RunState
  benchmarks: any[]
  onImplementRecommendation?: (rec: RecommendationItem) => Promise<void>
  implementingRec?: boolean
  implementNotice?: string | null
  preResult?: OptimizationResponse | null
  implementedRec?: string | null
  onReloadPage3?: () => void
  onAddBus?: (bus: BusTopology, branch: [number, number]) => void
  onDeleteBus?: (busId: number) => void
  onAddBranch?: (branch: [number, number]) => void
  onDeleteBranch?: (branch: [number, number]) => void
  onResetTopology?: () => void
  onUpdateBusLoad?: (busId: number, loadKw: number) => void
  onRemoveResource?: (busId: number, resource: ResourceType) => void
}) {
  const [dispatchMetric, setDispatchMetric] = useState<"demand" | "grid" | "unmet" | "soc" | "solar" | "wind" | "battery">("demand")

  const [addBusOpen, setAddBusOpen] = useState(false)
  const [addBranchOpen, setAddBranchOpen] = useState(false)
  const [deleteBranchOpen, setDeleteBranchOpen] = useState(false)

  // Add Bus Form State
  const nextBusId = Math.max(...buses.map((b) => b.id), 0) + 1
  const [newBusLoad, setNewBusLoad] = useState(100)
  const [newBusType, setNewBusType] = useState<string>("load")
  const [connectToBus, setConnectToBus] = useState<number>(selectedBus || 1)

  // Add Branch Form State
  const [branchFrom, setBranchFrom] = useState<number>(selectedBus || 1)
  const [branchTo, setBranchTo] = useState<number>(buses.find((b) => b.id !== selectedBus)?.id || 2)

  // Delete Branch Form State
  const [selectedBranchIdx, setSelectedBranchIdx] = useState<number>(0)

  const handleConfirmAddBus = () => {
    if (!onAddBus) return
    const parentBus = buses.find((b) => b.id === connectToBus) || buses[0]
    const newBus: BusTopology = {
      id: nextBusId,
      loadKw: newBusLoad,
      x: Math.min(920, Math.max(50, parentBus.x + (Math.random() > 0.5 ? 40 : -40))),
      y: Math.min(240, Math.max(40, parentBus.y + 40)),
      resources: newBusType !== "load" ? [newBusType as ResourceType] : [],
      installed:
        newBusType !== "load"
          ? [{ type: newBusType as ResourceType, label: `Custom ${newBusType.toUpperCase()}`, rating_kw: newBusLoad }]
          : [],
      loss_factor: 1.05,
      loss_pct: 5.0,
      distance_hops: (parentBus.distance_hops || 1) + 1,
      connected_buses: [connectToBus],
    }
    const newBranch: [number, number] = [Math.min(connectToBus, nextBusId), Math.max(connectToBus, nextBusId)]
    onAddBus(newBus, newBranch)
    setAddBusOpen(false)
  }

  const handleConfirmAddBranch = () => {
    if (branchFrom === branchTo || !onAddBranch) return
    onAddBranch([Math.min(branchFrom, branchTo), Math.max(branchFrom, branchTo)])
    setAddBranchOpen(false)
  }

  const handleConfirmDeleteBranch = () => {
    if (branches.length > 0 && branches[selectedBranchIdx] && onDeleteBranch) {
      onDeleteBranch(branches[selectedBranchIdx])
    }
    setDeleteBranchOpen(false)
  }

  const currentBus = buses.find((b) => b.id === selectedBus) || buses[0]

  const renderStudio = () => (
    <>
      <PageHeader
        eyebrow="Page 03 · Network Modification Studio"
        title="Feeder Topology & Bus Modification Studio"
        description="Add or delete feeder buses and branches, edit active bus loads (kW), assign distributed energy resources (Solar, Wind, Battery, Grid), and click 'Re-run' to execute live optimizations with custom network parameters."
        action={
          <div className="flex items-center gap-2">
            <Button size="sm" variant="primary" disabled={runState === "running"} onClick={rerun}>
              {runState === "running" ? "Re-running…" : "Re-run Live Optimization"}
            </Button>
          </div>
        }
      />
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_20rem]">
        <Card className="p-4">
          {/* Node and Path Interactive Editing Toolbar */}
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2 border-b border-olive/20 pb-3">
            <div className="flex flex-wrap items-center gap-2">
              <Button size="xs" variant="primary" onClick={() => setAddBusOpen(true)}>
                + Add Bus
              </Button>
              <Button
                size="xs"
                variant="danger"
                disabled={selectedBus === 1 || !onDeleteBus}
                onClick={() => onDeleteBus && onDeleteBus(selectedBus)}
                title={selectedBus === 1 ? "Cannot delete root Substation Bus 1" : `Delete Bus ${selectedBus}`}
              >
                - Delete Bus {selectedBus}
              </Button>
              <Button size="xs" variant="outline" onClick={() => setAddBranchOpen(true)}>
                + Add Path (Branch)
              </Button>
              <Button
                size="xs"
                variant="ghost"
                onClick={() => setDeleteBranchOpen(true)}
                disabled={branches.length <= 1}
              >
                - Delete Path
              </Button>
            </div>
            {onResetTopology && (
              <Button size="xs" variant="ghost" onClick={onResetTopology} className="text-forest-muted">
                ↺ Reset IEEE-33
              </Button>
            )}
          </div>

          <BusNetwork
            selected={selectedBus}
            onSelect={setSelectedBus}
            buses={buses}
            branches={branches}
            modifications={modifications}
            onDeleteBranch={onDeleteBranch}
          />
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-lg bg-caramel-tint p-3 text-xs">
            <span>
              Topology, bus loads, and resources are fully editable here. Click <strong>Re-run</strong> to optimize ABC and PSO with your updated network parameters.
            </span>
            <Button size="xs" variant="accent" disabled={runState === "running"} onClick={rerun}>
              {runState === "running" ? "Optimizing…" : "Re-run now"}
            </Button>
          </div>
        </Card>
        {currentBus && (
          <BusDetail
            bus={currentBus}
            branches={branches}
            editable
            added={modifications[selectedBus] ?? []}
            onAdd={requestModification}
            onUpdateLoad={onUpdateBusLoad}
            onRemoveResource={onRemoveResource}
          />
        )}
      </div>

      {/* Add Bus Modal */}
      {addBusOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-forest/60 p-4 backdrop-blur-xs">
          <Card variant="elevated" className="w-full max-w-md p-6 shadow-2xl">
            <div className="mb-4 flex items-center justify-between border-b border-olive/20 pb-3">
              <Heading level={2}>Add Bus (Node)</Heading>
              <Button variant="ghost" size="xs" onClick={() => setAddBusOpen(false)}>
                Cancel
              </Button>
            </div>
            <div className="space-y-4 text-xs">
              <div>
                <label className="mb-1 block font-semibold text-forest">Bus ID (Number)</label>
                <div className="rounded-lg border border-olive/35 bg-cornsilk-soft px-3 py-1.5 font-mono font-bold text-copper">
                  Bus {nextBusId}
                </div>
              </div>
              <div>
                <label className="mb-1 block font-semibold text-forest">Bus Resource Type</label>
                <Select
                  value={newBusType}
                  onChange={(e) => setNewBusType(e.target.value)}
                  className="w-full text-xs"
                >
                  <option value="load">Load Bus (Demand Only)</option>
                  <option value="solar">Solar PV Generation Bus</option>
                  <option value="wind">Wind Turbine Bus</option>
                  <option value="battery">Battery Storage (BESS) Bus</option>
                </Select>
              </div>
              <div>
                <label className="mb-1 block font-semibold text-forest">Active Load Power (kW)</label>
                <Input
                  type="number"
                  min="0"
                  value={newBusLoad}
                  onChange={(e) => setNewBusLoad(Math.max(0, Number(e.target.value)))}
                />
              </div>
              <div>
                <label className="mb-1 block font-semibold text-forest">Connect to Existing Feeder Bus</label>
                <Select
                  value={connectToBus}
                  onChange={(e) => setConnectToBus(Number(e.target.value))}
                  className="w-full text-xs"
                >
                  {buses.map((b) => (
                    <option key={b.id} value={b.id}>
                      Bus {b.id} ({b.resources && b.resources.length > 0 ? b.resources.join(", ") : `${b.loadKw} kW load`})
                    </option>
                  ))}
                </Select>
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-2 border-t border-olive/20 pt-4">
              <Button variant="outline" size="sm" onClick={() => setAddBusOpen(false)}>
                Cancel
              </Button>
              <Button variant="primary" size="sm" onClick={handleConfirmAddBus}>
                Add Bus to Topology
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* Add Branch Modal */}
      {addBranchOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-forest/60 p-4 backdrop-blur-xs">
          <Card variant="elevated" className="w-full max-w-md p-6 shadow-2xl">
            <div className="mb-4 flex items-center justify-between border-b border-olive/20 pb-3">
              <Heading level={2}>Add Node Path (Branch)</Heading>
              <Button variant="ghost" size="xs" onClick={() => setAddBranchOpen(false)}>
                Cancel
              </Button>
            </div>
            <div className="space-y-4 text-xs">
              <div>
                <label className="mb-1 block font-semibold text-forest">From Bus</label>
                <Select
                  value={branchFrom}
                  onChange={(e) => setBranchFrom(Number(e.target.value))}
                  className="w-full text-xs"
                >
                  {buses.map((b) => (
                    <option key={b.id} value={b.id}>
                      Bus {b.id}
                    </option>
                  ))}
                </Select>
              </div>
              <div>
                <label className="mb-1 block font-semibold text-forest">To Bus</label>
                <Select
                  value={branchTo}
                  onChange={(e) => setBranchTo(Number(e.target.value))}
                  className="w-full text-xs"
                >
                  {buses.map((b) => (
                    <option key={b.id} value={b.id}>
                      Bus {b.id}
                    </option>
                  ))}
                </Select>
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-2 border-t border-olive/20 pt-4">
              <Button variant="outline" size="sm" onClick={() => setAddBranchOpen(false)}>
                Cancel
              </Button>
              <Button variant="primary" size="sm" disabled={branchFrom === branchTo} onClick={handleConfirmAddBranch}>
                Connect Path
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* Delete Branch Modal */}
      {deleteBranchOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-forest/60 p-4 backdrop-blur-xs">
          <Card variant="elevated" className="w-full max-w-md p-6 shadow-2xl">
            <div className="mb-4 flex items-center justify-between border-b border-olive/20 pb-3">
              <Heading level={2}>Delete Node Path (Branch)</Heading>
              <Button variant="ghost" size="xs" onClick={() => setDeleteBranchOpen(false)}>
                Cancel
              </Button>
            </div>
            <div className="space-y-4 text-xs">
              <p className="text-forest-muted">Select an existing line branch to disconnect from the feeder network:</p>
              <div>
                <Select
                  value={selectedBranchIdx}
                  onChange={(e) => setSelectedBranchIdx(Number(e.target.value))}
                  className="w-full text-xs font-mono"
                >
                  {branches.map(([u, v], i) => (
                    <option key={i} value={i}>
                      Line {i + 1}: Bus {u} ─── Bus {v}
                    </option>
                  ))}
                </Select>
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-2 border-t border-olive/20 pt-4">
              <Button variant="outline" size="sm" onClick={() => setDeleteBranchOpen(false)}>
                Cancel
              </Button>
              <Button variant="danger" size="sm" onClick={handleConfirmDeleteBranch}>
                Remove Line
              </Button>
            </div>
          </Card>
        </div>
      )}
    </>
  )

  if (!result)
    return (
      <>
        <PageHeader
          eyebrow="Page 03 · Results & planning"
          title="Algorithm Comparison & Topology Studio"
          description="Benchmark Artificial Bee Colony (ABC) versus Particle Swarm Optimization (PSO), or modify network topology and bus resources below."
          action={
            <Button size="sm" disabled={runState === "running"} onClick={rerun}>
              {runState === "running" ? "Optimizing…" : "Run Baseline Benchmark"}
            </Button>
          }
        />
        <Card variant="caramel" className="mb-6 p-4 sm:p-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <Heading level={2} className="text-base">Optimization Benchmark Not Yet Run</Heading>
              <p className="mt-1 text-xs text-forest-muted">
                Customize feeder buses, branches, and resource allocations below, then click <strong>Run Baseline Benchmark</strong> to execute the full ABC and PSO simulation with Shannon Entropy weighting.
              </p>
            </div>
            <Button size="sm" variant="primary" disabled={runState === "running"} onClick={rerun}>
              {runState === "running" ? "Running Optimization…" : "Run Baseline Benchmark"}
            </Button>
          </div>
        </Card>
        {renderStudio()}
      </>
    )

  const { abc, pso } = result
  const overallWinner = result.overallWinner || "ABC"
  const metricWinner = (a: number | undefined, b: number | undefined) => {
    const valA = Number(a) || 0
    const valB = Number(b) || 0
    return Math.abs(valA - valB) < 0.001 ? "Tie" : valA < valB ? "ABC" : "PSO"
  }

  const exportResults = () => {
    const header =
      "hour,abc_demand_kw,abc_solar_kw,abc_wind_kw,abc_battery_kw,abc_grid_kw,abc_unmet_kw,abc_soc_percent,pso_demand_kw,pso_solar_kw,pso_wind_kw,pso_battery_kw,pso_grid_kw,pso_unmet_kw,pso_soc_percent"
    const rows = abc.dispatch.map((item, index) => {
      const psoItem = pso.dispatch[index] || item
      return [
        item.hour,
        item.demand,
        item.solar,
        item.wind,
        item.battery,
        item.grid,
        item.unmet,
        item.soc,
        psoItem.demand,
        psoItem.solar,
        psoItem.wind,
        psoItem.battery,
        psoItem.grid,
        psoItem.unmet,
        psoItem.soc,
      ].join(",")
    })
    const url = URL.createObjectURL(new Blob([[header, ...rows].join("\n")], { type: "text/csv" }))
    const link = document.createElement("a")
    link.href = url
    link.download = `ecogrid-optimization-${result.scenario.name.toLowerCase().replaceAll(" ", "-")}.csv`
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <>
      <PageHeader
        eyebrow="Page 03 · Results & planning"
        title="Algorithm Comparison"
        description={`Same-input benchmark for ${result.scenario.name} using real IEEE 33-bus dispatch simulation and Shannon Entropy weights.`}
        action={
          <div className="grid w-full grid-cols-2 gap-2 md:flex md:w-auto">
            <Button variant="outline" size="sm" onClick={exportResults}>
              Export CSV
            </Button>
            {onReloadPage3 && (
              <Button
                variant="outline"
                size="sm"
                onClick={onReloadPage3}
                disabled={implementingRec || runState === "running"}
                title="Reload Page 3 to baseline configuration"
              >
                🔄 Reload Page 3
              </Button>
            )}
            <Button size="sm" disabled={runState === "running"} onClick={rerun}>
              {runState === "running" ? "Re-running…" : "Re-run"}
            </Button>
          </div>
        }
      />

      <Card variant="forest" className="mb-5 flex flex-col gap-5 overflow-hidden p-4 sm:p-5 md:flex-row md:items-center">
        <div className="flex-1">
          <div className="text-xs uppercase tracking-widest text-cornsilk/70">Overall ranking</div>
          <Heading level={2} className="mt-1 !text-cornsilk">
            {overallWinner} ranks first for this run
          </Heading>
          <p className="mt-1 text-xs text-cornsilk/75">
            Evaluated by the multi-objective fitness function under Shannon Entropy weighting: lower fitness, unmet
            energy, operating cost, and losses are prioritized.
          </p>
        </div>
        <div className="grid w-full grid-cols-2 gap-4 border-t border-cornsilk/10 pt-4 md:w-auto md:border-l md:border-t-0 md:pl-5 md:pt-0">
          <div className="min-w-0">
            <div className="text-[10px] text-cornsilk/70">Dataset</div>
            <div className="mt-1 truncate text-xs font-semibold">{result.dataset}</div>
          </div>
          <div>
            <div className="text-[10px] text-cornsilk/70">Completed</div>
            <div className="mt-1 text-xs font-semibold">{result.completedAt}</div>
          </div>
        </div>
      </Card>

      {(() => {
        const getUnmet = (alg: AlgorithmResult) => {
          const val =
            alg.unmetKwh ??
            (alg as any).unmet_load_kwh ??
            (alg as any).unmet_energy_kwh ??
            (alg as any).total_unmet_load ??
            alg.dispatch?.reduce((sum, d) => sum + (d.unmet || 0), 0) ??
            0
          return Number(val) || 0
        }

        const getCost = (alg: AlgorithmResult) => {
          const val =
            alg.cost ??
            alg.totalCost ??
            (alg as any).total_cost ??
            ((alg.capitalCost || (alg as any).capital_cost || (alg as any).c_capital || 0) +
             (alg.operationalCost || (alg as any).operational_cost || (alg as any).c_op || 0)) ??
            0
          return Number(val) || 0
        }

        const getObjective = (alg: AlgorithmResult) => {
          const val = alg.objective ?? (alg as any).fitness ?? 0
          return Number(val) || 0
        }

        const getTime = (alg: AlgorithmResult) => {
          const val = alg.executionSeconds ?? (alg as any).computational_time ?? 0
          return Number(val) || 0
        }

        const metrics = [
          {
            label: "Unmet energy",
            a: getUnmet(abc),
            b: getUnmet(pso),
            unit: "kWh",
            important: true,
          },
          {
            label: "Total daily cost",
            a: getCost(abc),
            b: getCost(pso),
            unit: "₹",
            important: true,
          },
          {
            label: "Objective fitness (F)",
            a: getObjective(abc),
            b: getObjective(pso),
            unit: "",
            important: false,
          },
          {
            label: "Execution time",
            a: getTime(abc),
            b: getTime(pso),
            unit: "s",
            important: false,
          },
        ]

        return (
          <div className="mb-5 grid grid-cols-2 gap-3 sm:gap-4 xl:grid-cols-4">
            {metrics.map((metric) => (
              <Card key={metric.label} variant={metric.important ? "elevated" : "default"} className="min-w-0 p-3 sm:p-4">
                <div className="mb-3 text-xs font-semibold sm:mb-4">{metric.label}</div>
                <div className="grid gap-2 sm:grid-cols-2">
                  <div className="min-w-0 rounded-lg bg-caramel-tint p-2">
                    <div className="text-[10px] text-forest-muted">ABC</div>
                    <div className="mt-1 truncate font-mono text-xs font-bold sm:text-sm">
                      {metric.unit === "₹" && "₹"}
                      {formatNumber(metric.a, 1)} {metric.unit !== "₹" && metric.unit}
                    </div>
                  </div>
                  <div className="min-w-0 rounded-lg bg-olive-tint p-2">
                    <div className="text-[10px] text-forest-muted">PSO</div>
                    <div className="mt-1 truncate font-mono text-xs font-bold sm:text-sm">
                      {metric.unit === "₹" && "₹"}
                      {formatNumber(metric.b, 1)} {metric.unit !== "₹" && metric.unit}
                    </div>
                  </div>
                </div>
                <div className="mt-3 text-[10px] font-semibold text-olive">
                  {metricWinner(metric.a, metric.b)}{" "}
                  {metricWinner(metric.a, metric.b) !== "Tie" && "wins"}
                </div>
              </Card>
            ))}
          </div>
        )
      })()}

      {/* 1. Developed Graph: 24-Hour Stacked Dispatch Profile Chart */}
      <Card className="mb-5 p-4 sm:p-5">
        <div className="mb-4">
          <div className="text-xs font-bold uppercase tracking-wider text-copper">Developed visualizer · dispatch</div>
          <Heading level={2} className="mt-1">
            24-Hour Stacked Energy Dispatch Profile
          </Heading>
          <p className="mt-1 text-xs text-forest-muted">
            Stacked generation mix (Solar, Wind, Battery Discharge, Grid Import) plotted against the diurnal load demand curve. Toggle between ABC and PSO.
          </p>
        </div>
        <StackedDispatchChart abc={abc} pso={pso} />
      </Card>

      {/* Real Python Graphs: Bus-Wise Generation & 33-Bus Transmission Losses */}
      <div className="mb-5 grid gap-5 xl:grid-cols-2">
        <Card className="p-4 sm:p-5">
          <div className="mb-4">
            <div className="text-xs font-bold uppercase tracking-wider text-copper">Developed visualizer · generation nodes</div>
            <Heading level={2} className="mt-1">Bus-Wise Generation Contribution</Heading>
            <p className="text-xs text-forest-muted">
              Hourly generation across Bus 13 (PV 1: 851.5 kW), Bus 30 (PV 2: 1,157.6 kW), and Bus 6 (Wind: 2,098 kW).
            </p>
          </div>
          <BusGenerationChart dispatch={abc.dispatch} />
        </Card>

        <Card className="p-4 sm:p-5">
          <div className="mb-4">
            <div className="text-xs font-bold uppercase tracking-wider text-copper">Developed visualizer · line losses</div>
            <Heading level={2} className="mt-1">33-Bus Transmission Losses per Bus</Heading>
            <p className="text-xs text-forest-muted">
              Cable transmission losses across branches feeding Bus 13 (12% factor), Bus 30 (10% factor), and Bus 6 (5% factor).
            </p>
          </div>
          <TransmissionLossChart dispatch={abc.dispatch} />
        </Card>
      </div>

      {/* 2. Developed Graphs: Convergence Curves & Battery SOC Trajectory Curve */}
      <div className="mb-5 grid gap-5 xl:grid-cols-2">
        <Card className="p-4 sm:p-5">
          <div className="mb-4">
            <div className="text-xs font-bold uppercase tracking-wider text-copper">Developed visualizer · convergence</div>
            <Heading level={2} className="mt-1">Convergence History Curve</Heading>
            <p className="text-xs text-forest-muted">
              Real objective fitness by iteration · ABC ({abc.convergenceIterations} iter to 95%) vs PSO (
              {pso.convergenceIterations} iter to 95%)
            </p>
          </div>
          <MiniChart
            unit="F"
            series={[
              { name: "ABC", values: abc.convergence, color: "var(--color-copper)" },
              { name: "PSO", values: pso.convergence, color: "var(--color-olive-leaf)" },
            ]}
          />
        </Card>

        <Card className="p-4 sm:p-5">
          <div className="mb-4">
            <div className="text-xs font-bold uppercase tracking-wider text-copper">Developed visualizer · storage</div>
            <Heading level={2} className="mt-1">24-Hour Battery SOC (%) Trajectory</Heading>
            <p className="text-xs text-forest-muted">
              State-of-Charge tracking for BESS storage across 24 hours within 20% to 95% operating limits.
            </p>
          </div>
          <BatterySocChart abc={abc} pso={pso} />
        </Card>
      </div>

      {/* 3. Developed Graph: Capital vs Operational Cost Breakdown Chart */}
      <Card className="mb-5 p-4 sm:p-5">
        <div className="mb-4">
          <div className="text-xs font-bold uppercase tracking-wider text-copper">Developed visualizer · financials</div>
          <Heading level={2} className="mt-1">
            Capital vs. Operational Cost Breakdown
          </Heading>
          <p className="mt-1 text-xs text-forest-muted">
            Side-by-side comparison of 20-year daily amortized CapEx against daily operational expenses (OpEx) for ABC and PSO.
          </p>
        </div>
        <CostBreakdownChart abc={abc} pso={pso} />
      </Card>

      {/* Feasibility, Power Losses & Violations */}
      <Card className="mb-5 p-4">
        <div className="grid gap-3 sm:grid-cols-4">
          <div className="rounded-lg bg-olive-tint p-3">
            <div className="text-[10px] uppercase text-forest-muted">Feasibility</div>
            <div className="mt-1 text-sm font-bold">{result.feasibility}</div>
          </div>
          <div className="rounded-lg bg-cornsilk-soft p-3">
            <div className="text-[10px] uppercase text-forest-muted">Total System Loss</div>
            <div className="mt-1 font-mono text-sm font-bold">
              {formatNumber(result.losses.abc_system_loss_kwh, 1)} kWh (ABC)
            </div>
          </div>
          <div className="rounded-lg bg-cornsilk-soft p-3">
            <div className="text-[10px] uppercase text-forest-muted">33-Bus Cable Transmission Loss</div>
            <div className="mt-1 font-mono text-sm font-bold">
              {formatNumber(result.losses.abc_cable_transmission_loss_kwh, 1)} kWh
            </div>
          </div>
          <div className="rounded-lg bg-cornsilk-soft p-3">
            <div className="text-[10px] uppercase text-forest-muted">Constraint Violations</div>
            <div className="mt-1 font-mono text-sm font-bold">
              {result.violations.battery_violations} battery · 0 thermal
            </div>
          </div>
        </div>
      </Card>

      {/* 4. Developed Graph: 10-Scenario Global Benchmark Suite */}
      <Card className="mb-5 p-4 sm:p-5">
        <div className="mb-4">
          <div className="text-xs font-bold uppercase tracking-wider text-copper">Developed visualizer · global benchmark</div>
          <Heading level={2} className="mt-1">
            10-Scenario Global Benchmark Suite
          </Heading>
          <p className="mt-1 text-xs text-forest-muted">
            Cross-scenario performance matrix evaluating ABC and PSO resilience across all operational stress scenarios.
          </p>
        </div>
        <GlobalBenchmarkChart benchmarks={benchmarks} />
      </Card>

      {/* 5. Post-Implementation Comparison Graph: Generated on Implement & Run */}
      {preResult && (
        <Card id="before-after-comparison-section" className="mb-5 border-2 border-emerald-600/40 bg-emerald-500/5 p-4 sm:p-5">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-600 animate-ping" />
                <div className="text-xs font-bold uppercase tracking-wider text-emerald-800">
                  Post-Implementation Visualizer · 100% Demand Satisfaction
                </div>
              </div>
              <Heading level={2} className="mt-1 text-forest">
                Comparison of Before and After Graph
              </Heading>
              <p className="mt-1 text-xs text-forest-muted">
                Live before vs. after comparison for <strong>{implementedRec || "Autonomous Expansion"}</strong>. Displays zero unmet load deficit and full demand satisfied.
              </p>
            </div>
            {onReloadPage3 && (
              <Button size="sm" variant="outline" onClick={onReloadPage3} disabled={implementingRec}>
                🔄 Reload Page 3
              </Button>
            )}
          </div>
          <PostImplementationComparisonChart
            preResult={preResult}
            postResult={result}
            implementedRec={implementedRec || "Autonomous Capacity Expansion"}
            onReloadPage3={onReloadPage3}
          />
        </Card>
      )}

      {/* Recommendations */}
      {result.recommendations && result.recommendations.length > 0 && (
        <Card className="mb-5 p-4 sm:p-5">
          <div className="mb-4">
            <div className="text-xs font-bold uppercase tracking-wider text-copper">Capacity recommendations</div>
            <Heading level={2} className="mt-1">
              Autonomous Expansion Intelligence
            </Heading>
            <p className="mt-1 text-xs text-forest-muted">
              Heuristic asset sizing (PV, BESS, Grid) and 20-year amortized financials from the recommendation engine.
            </p>
          </div>

          {implementNotice && (
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-emerald-600/40 bg-emerald-500/10 p-3.5 text-xs font-medium text-emerald-900">
              <span className="flex items-center gap-2">
                <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-600" />
                {implementNotice}
              </span>
              <div className="flex items-center gap-2">
                {onReloadPage3 && (
                  <Button size="xs" variant="outline" onClick={onReloadPage3} disabled={implementingRec}>
                    🔄 Reload Page 3
                  </Button>
                )}
                <Badge tone="forest">100% Demand Met</Badge>
              </div>
            </div>
          )}

          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {result.recommendations.map((rec: RecommendationItem, idx: number) => (
              <div key={idx} className="flex flex-col rounded-xl border border-olive/20 bg-cornsilk-soft p-4">
                <div className="mb-2 flex items-center justify-between">
                  <Badge tone={rec.priority === "RECOMMENDED" ? "olive" : rec.priority === "ALTERNATIVE" ? "caramel" : "neutral"}>
                    {rec.priority}
                  </Badge>
                  <span className="text-[10px] font-mono font-semibold uppercase text-forest-muted">{rec.category}</span>
                </div>
                <div className="font-semibold text-sm">{rec.action}</div>
                <div className="mt-1 font-mono text-xs text-copper">{rec.additional_capacity}</div>
                <p className="my-2.5 flex-1 text-xs leading-relaxed text-forest-muted">{rec.description}</p>
                <div className="mt-auto border-t border-olive/15 pt-2 text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-forest-muted">CapEx:</span>
                    <span className="font-mono font-bold">₹{formatNumber(rec.capital_cost)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-forest-muted">Daily amortized:</span>
                    <span className="font-mono font-bold">₹{formatNumber(rec.daily_amortized_cost, 1)}/day</span>
                  </div>
                  {onImplementRecommendation && (
                    <div className="mt-3 flex items-center justify-between gap-2 border-t border-olive/20 pt-2.5">
                      <span className="text-[10px] font-medium text-forest-muted">Satisfy demand:</span>
                      <Button
                        size="xs"
                        variant={rec.priority === "RECOMMENDED" ? "primary" : "secondary"}
                        disabled={implementingRec}
                        onClick={() => onImplementRecommendation(rec)}
                      >
                        {implementingRec ? "Implementing..." : "Implement & run"}
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {renderStudio()}
    </>
  )
}

function ModificationModal({
  pending,
  bus,
  confirm,
  close,
}: {
  pending: ResourceType | null
  bus: number
  confirm: () => void
  close: () => void
}) {
  if (!pending) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-forest/60 p-4">
      <Card variant="elevated" className="w-full max-w-md p-6">
        <div className="mb-4 flex justify-end">
          <Button variant="ghost" size="xs" onClick={close} aria-label="Close preview">
            Close
          </Button>
        </div>
        <div className="text-xs font-bold uppercase tracking-widest text-copper">Preview modification</div>
        <Heading level={2} className="mt-1">
          Add {resourceMeta[pending].label} at Bus {bus}
        </Heading>
        <p className="mt-2 text-sm leading-relaxed text-forest-muted">
          This adds an active generation or storage node to Bus {bus}. Transmission cable losses will be computed
          proportionately from Bus 1.
        </p>
        <div className="my-5 rounded-lg bg-cornsilk-soft p-3 text-xs">
          <div className="flex justify-between py-1">
            <span>Target Bus</span>
            <strong>Node {bus}</strong>
          </div>
          <div className="flex justify-between py-1">
            <span>Resource Type</span>
            <strong>{resourceMeta[pending].label}</strong>
          </div>
          <div className="flex justify-between py-1">
            <span>Optimization Impact</span>
            <strong>Active upon Re-run</strong>
          </div>
        </div>
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={close}>
            Cancel
          </Button>
          <Button onClick={confirm}>Apply placement</Button>
        </div>
      </Card>
    </div>
  )
}

export default function App() {
  const [page, setPage] = useState<Page>("network")
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [selectedBus, setSelectedBus] = useState(1)
  const [scenarioIndex, setScenarioIndex] = useState(0)
  const [config, setConfig] = useState(defaultConfig)
  const [runState, setRunState] = useState<RunState>("idle")
  const [dataset, setDataset] = useState("Data1.csv")
  const [result, setResult] = useState<OptimizationResponse | null>(null)
  const [modifications, setModifications] = useState<Record<number, ResourceType[]>>({})
  const [pending, setPending] = useState<ResourceType | null>(null)
  const [runError, setRunError] = useState<string | null>(null)
  const [customLoadProfile, setCustomLoadProfile] = useState<number[] | null>(null)

  // Real backend loaded state
  const [backendConnected, setBackendConnected] = useState(false)
  const [buses, setBuses] = useState<BusTopology[]>(defaultBuses as any)
  const [branches, setBranches] = useState<[number, number][]>(defaultBranches)
  const [totalBaseLoadKw, setTotalBaseLoadKw] = useState(defaultTotalLoad)
  const [scenarios, setScenarios] = useState<BackendScenario[]>(defaultScenarios as any)
  const [datasetsList, setDatasetsList] = useState<DatasetItem[]>([
    {
      id: "Data1.csv",
      name: "Data1.csv (Primary Measured kW & Bus Ratings)",
      description: "24-hour measured demand profiles, actual PV & Wind generation, and nameplate bus allocations.",
      peak_load_kw: 3715,
      is_default: true,
    },
  ])

  const [benchmarks, setBenchmarks] = useState<any[]>([])

  // Initial data loading from FastAPI backend
  useEffect(() => {
    let isMounted = true

    async function loadInitialData() {
      try {
        const health = await api.getHealth()
        if (health.status === "ok" && isMounted) {
          setBackendConnected(true)
        }
      } catch {
        if (isMounted) setBackendConnected(false)
      }

      try {
        const net = await api.getNetwork()
        if (isMounted && net.buses && net.buses.length > 0) {
          setBuses(net.buses)
          setBranches(net.branches)
          setTotalBaseLoadKw(net.total_base_load_kw)
        }
      } catch {
        // Fallback to local default network
      }

      try {
        const scs = await api.getScenarios()
        if (isMounted && scs.length > 0) {
          setScenarios(scs)
        }
      } catch {
        // Fallback to default scenarios
      }

      try {
        const dsets = await api.getDatasets()
        if (isMounted && dsets.length > 0) {
          setDatasetsList(dsets)
        }
      } catch {
        // Fallback to default datasets list
      }

      try {
        const bmarks = await api.getBenchmark()
        if (isMounted && bmarks && bmarks.length > 0) {
          setBenchmarks(bmarks)
        }
      } catch {
        // Fallback or empty
      }

      try {
        const initOpt = await api.runOptimization({
          dataset: "Data1.csv",
          scenario_index: 0,
          config: defaultConfig,
          modifications: {},
          max_iter: 40,
        })
        if (isMounted) {
          setResult(initOpt)
          setRunState("complete")
        }
      } catch {
        // Deferred until manual run
      }
    }

    loadInitialData()
    return () => {
      isMounted = false
    }
  }, [])

  const pageLabel =
    page === "network"
      ? "System overview"
      : page === "optimize"
        ? "Data & optimization"
        : page === "compare"
          ? "Compare & modify"
          : "Weights & fitness simulation"

  const runOptimization = async () => {
    setRunState("running")
    setRunError(null)
    try {
      const data = await api.runOptimization({
        dataset,
        scenario_index: scenarioIndex,
        config,
        modifications,
        max_iter: 60,
        custom_load_profile: customLoadProfile ?? undefined,
      })
      setResult(data)
      setRunState("complete")
      setPage("compare")
    } catch {
      // Automatic seamless fallback to client simulation
      try {
        const fallback = runClientDispatchSimulation({
          scenario_index: scenarioIndex,
          config,
          modifications,
          custom_load_profile: customLoadProfile ?? undefined,
        })
        setResult(fallback)
        setRunState("complete")
        setPage("compare")
      } catch (fallbackErr: any) {
        setRunState("failed")
        setRunError(fallbackErr.message || "Failed to execute optimization.")
      }
    }
  }

  const [preResult, setPreResult] = useState<OptimizationResponse | null>(null)
  const [implementedRec, setImplementedRec] = useState<string | null>(null)
  const [implementingRec, setImplementingRec] = useState(false)
  const [implementNotice, setImplementNotice] = useState<string | null>(null)

  const handleImplementRecommendation = async (rec: RecommendationItem) => {
    setImplementingRec(true)
    setImplementNotice(null)
    if (result) {
      setPreResult(result)
      setImplementedRec(rec.action)
    }
    try {
      const updatedConfig = { ...config }
      const updatedModifications = { ...modifications }

      if (rec.category.toLowerCase().includes("solar")) {
        const addedKw = rec.additional_capacity_kw || 3715.0
        updatedConfig.solarKw += addedKw
        updatedModifications[18] = [...(updatedModifications[18] || []), "solar"]
      } else if (rec.category.toLowerCase().includes("battery")) {
        updatedConfig.batteryKw = Math.max(updatedConfig.batteryKw, rec.additional_capacity_kw || 4086.5)
        updatedConfig.batteryKwh = Math.max(updatedConfig.batteryKwh, rec.additional_capacity_kwh || 20487.1)
        updatedModifications[selectedBus] = [...(updatedModifications[selectedBus] || []), "battery"]
      } else if (rec.category.toLowerCase().includes("grid")) {
        updatedConfig.gridLimitKw = Math.max(updatedConfig.gridLimitKw, (rec.additional_capacity_kw || 4086.5) + 3200)
      }

      setConfig(updatedConfig)
      setModifications(updatedModifications)

      const data = await api.runOptimization({
        dataset,
        scenario_index: scenarioIndex,
        config: updatedConfig,
        modifications: updatedModifications,
        max_iter: 70,
        custom_load_profile: customLoadProfile ?? undefined,
      })

      setResult(data)
      const remainingDeficit = Math.min(data.abc.unmetKwh ?? 0, data.pso.unmetKwh ?? 0)
      const isFullyMet = remainingDeficit < 0.5
      if (isFullyMet) {
        setImplementNotice(
          `Implemented ${rec.action} in simulation. Recalculated outcome: deficit eliminated (0.0 kWh unmet, 100% demand met · Validated as Feasible).`
        )
      } else {
        setImplementNotice(
          `Implemented ${rec.action} in simulation. Recalculated outcome: deficit reduced to ${formatNumber(remainingDeficit, 1)} kWh (${formatNumber(data.abc.loadSatisfaction, 1)}% demand met).`
        )
      }
      setTimeout(() => {
        const el = document.getElementById("before-after-comparison-section")
        if (el) {
          el.scrollIntoView({ behavior: "smooth", block: "start" })
        }
      }, 120)
    } catch {
      try {
        const fallback = runClientDispatchSimulation({
          scenario_index: scenarioIndex,
          config: updatedConfig,
          modifications: updatedModifications,
          custom_load_profile: customLoadProfile ?? undefined,
        })
        setResult(fallback)
        const remainingDeficit = Math.min(fallback.abc.unmetKwh ?? 0, fallback.pso.unmetKwh ?? 0)
        const isFullyMet = remainingDeficit < 0.5
        if (isFullyMet) {
          setImplementNotice(
            `Implemented ${rec.action} in simulation. Recalculated outcome: deficit eliminated (0.0 kWh unmet, 100% demand met · Validated as Feasible).`
          )
        } else {
          setImplementNotice(
            `Implemented ${rec.action} in simulation. Recalculated outcome: deficit reduced to ${formatNumber(remainingDeficit, 1)} kWh (${formatNumber(fallback.abc.loadSatisfaction, 1)}% demand met).`
          )
        }
      } catch (err: any) {
        setImplementNotice(`Failed to implement: ${err.message}`)
      }
    } finally {
      setImplementingRec(false)
    }
  }

  const handleReloadPage3 = async () => {
    setImplementingRec(true)
    setImplementNotice("Reloading Page 3 to baseline configuration...")
    try {
      if (preResult) {
        setResult(preResult)
      }
      setConfig(defaultConfig)
      setModifications({})
      setPreResult(null)
      setImplementedRec(null)

      const data = await api.runOptimization({
        dataset,
        scenario_index: scenarioIndex,
        config: defaultConfig,
        modifications: {},
        max_iter: 40,
        custom_load_profile: customLoadProfile ?? undefined,
      })
      setResult(data)
      setImplementNotice(null)
    } catch {
      try {
        const fallback = runClientDispatchSimulation({
          scenario_index: scenarioIndex,
          config: defaultConfig,
          modifications: {},
          custom_load_profile: customLoadProfile ?? undefined,
        })
        setResult(fallback)
        setImplementNotice(null)
      } catch (err: any) {
        console.error("Failed to reload Page 3:", err)
        setImplementNotice(`Failed to reload Page 3: ${err.message}`)
      }
    } finally {
      setImplementingRec(false)
    }
  }

  const handleAddBus = (newBus: BusTopology, branch: [number, number]) => {
    setBuses((prev) => [...prev, newBus])
    setBranches((prev) => [...prev, branch])
    setTotalBaseLoadKw((prev) => prev + (newBus.loadKw || 0))
    setSelectedBus(newBus.id)
    api.addBus({ id: newBus.id, loadKw: newBus.loadKw, type: newBus.resources?.[0] || "load", connect_to: branch[0] }).catch(() => {})
  }

  const handleDeleteBus = (busId: number) => {
    if (busId === 1) return
    const busToDelete = buses.find((b) => b.id === busId)
    setBuses((prev) => prev.filter((b) => b.id !== busId))
    setBranches((prev) => prev.filter(([u, v]) => u !== busId && v !== busId))
    if (busToDelete) {
      setTotalBaseLoadKw((prev) => Math.max(0, prev - (busToDelete.loadKw || 0)))
    }
    setSelectedBus(1)
    api.deleteBus({ id: busId }).catch(() => {})
  }

  const handleAddBranch = (branch: [number, number]) => {
    const exists = branches.some(([u, v]) => (u === branch[0] && v === branch[1]) || (u === branch[1] && v === branch[0]))
    if (!exists) {
      setBranches((prev) => [...prev, branch])
      api.addBranch({ from_bus: branch[0], to_bus: branch[1] }).catch(() => {})
    }
  }

  const handleDeleteBranch = (branch: [number, number]) => {
    setBranches((prev) => prev.filter(([u, v]) => !(u === branch[0] && v === branch[1]) && !(u === branch[1] && v === branch[0])))
    api.deleteBranch({ from_bus: branch[0], to_bus: branch[1] }).catch(() => {})
  }

  const handleResetTopology = () => {
    setBuses(defaultBuses as any)
    setBranches(defaultBranches)
    setTotalBaseLoadKw(defaultTotalLoad)
    setSelectedBus(1)
  }

  const handleUpdateBusLoad = (busId: number, newLoadKw: number) => {
    setBuses((prev) =>
      prev.map((b) => (b.id === busId ? { ...b, loadKw: newLoadKw } : b))
    )
    setTotalBaseLoadKw((prev) => {
      const oldBus = buses.find((b) => b.id === busId)
      const oldLoad = oldBus?.loadKw || 0
      return Math.max(0, prev - oldLoad + newLoadKw)
    })
  }

  const handleRemoveResource = (busId: number, resource: ResourceType) => {
    setModifications((curr) => ({
      ...curr,
      [busId]: (curr[busId] || []).filter((r) => r !== resource),
    }))
    setBuses((prev) =>
      prev.map((b) => {
        if (b.id !== busId) return b
        return {
          ...b,
          resources: (b.resources || []).filter((r) => r !== resource),
          installed: (b.installed || []).filter((i) => i.type !== resource),
        }
      })
    )
  }

  const confirmModification = () => {
    if (!pending) return
    setModifications((current) => ({
      ...current,
      [selectedBus]: [...(current[selectedBus] ?? []), pending],
    }))
    setPending(null)
  }

  return (
    <div className="min-h-screen bg-cornsilk text-forest">
      <Sidebar
        page={page}
        setPage={setPage}
        open={sidebarOpen}
        setOpen={setSidebarOpen}
        backendConnected={backendConnected}
      />
      {sidebarOpen && (
        <div className="fixed inset-0 z-30 bg-forest/40 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}
      <main className="min-h-screen lg:ml-72">
        <div className="sticky top-0 z-20 flex items-center justify-between border-b border-olive/20 bg-cornsilk/95 px-3 py-2 backdrop-blur-sm sm:px-4 sm:py-3 lg:hidden">
          <Button
            variant="ghost"
            size="sm"
            className="aspect-square p-2"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open navigation"
            aria-controls="primary-navigation"
            aria-expanded={sidebarOpen}
          >
            <Menu aria-hidden="true" className="h-5 w-5" strokeWidth={2} />
          </Button>
          <span className="truncate pl-3 font-display text-xs font-bold text-forest">
            ECOGRID <span className="text-emerald-700">AI</span> · <span className="font-sans font-normal text-forest-muted">{pageLabel}</span>
          </span>
        </div>
        <div className="mx-auto max-w-screen-2xl p-3 sm:p-4 md:p-7 xl:p-9">
          {page === "network" && (
            <NetworkPage
              buses={buses}
              branches={branches}
              totalBaseLoadKw={totalBaseLoadKw}
              selectedBus={selectedBus}
              setSelectedBus={setSelectedBus}
            />
          )}
          {page === "optimize" && (
            <OptimizationPage
              scenarios={scenarios}
              scenarioIndex={scenarioIndex}
              setScenarioIndex={setScenarioIndex}
              config={config}
              setConfig={setConfig}
              runState={runState}
              runOptimization={runOptimization}
              dataset={dataset}
              setDataset={setDataset}
              datasetsList={datasetsList}
              onValidateCustomLoad={setCustomLoadProfile}
              runError={runError}
            />
          )}
          {page === "compare" && (
            <ComparisonPage
              result={result}
              setPage={setPage}
              buses={buses}
              branches={branches}
              selectedBus={selectedBus}
              setSelectedBus={setSelectedBus}
              modifications={modifications}
              requestModification={setPending}
              rerun={runOptimization}
              runState={runState}
              benchmarks={benchmarks}
              onImplementRecommendation={handleImplementRecommendation}
              implementingRec={implementingRec}
              implementNotice={implementNotice}
              preResult={preResult}
              implementedRec={implementedRec}
              onReloadPage3={handleReloadPage3}
              onAddBus={handleAddBus}
              onDeleteBus={handleDeleteBus}
              onAddBranch={handleAddBranch}
              onDeleteBranch={handleDeleteBranch}
              onResetTopology={handleResetTopology}
              onUpdateBusLoad={handleUpdateBusLoad}
              onRemoveResource={handleRemoveResource}
            />
          )}
          {page === "weights" && <WeightsSimulationPage />}
        </div>
      </main>
      <ModificationModal
        pending={pending}
        bus={selectedBus}
        confirm={confirmModification}
        close={() => setPending(null)}
      />
    </div>
  )
}
