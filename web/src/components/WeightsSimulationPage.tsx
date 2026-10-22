import { useState } from "react"
import { Badge, Button, Card, Heading, Input, Select } from "./ui/Primitives"
import { Sliders, Activity, Sparkles, Calculator, Check, ArrowRight } from "lucide-react"

function formatNumber(value: number, digits = 0) {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: digits }).format(value)
}

// 10 Scenarios Decision Matrix for Shannon Entropy calculation
const DECISION_MATRIX = [
  { scenario: "Normal Operation", cap: 57520, op: 273444, loss: 2763, unmet: 3070, curtail: 11932 },
  { scenario: "Peak Summer", cap: 57520, op: 324954, loss: 3120, unmet: 17072, curtail: 4500 },
  { scenario: "Winter Low Solar", cap: 57520, op: 273300, loss: 2450, unmet: 8200, curtail: 7100 },
  { scenario: "Wind Drought", cap: 57520, op: 310500, loss: 2980, unmet: 14500, curtail: 2100 },
  { scenario: "High Renewable", cap: 57520, op: 243800, loss: 3450, unmet: 1200, curtail: 28400 },
  { scenario: "Grid Failure", cap: 57520, op: 55400, loss: 1890, unmet: 22400, curtail: 8900 },
  { scenario: "Battery Degraded", cap: 42000, op: 288600, loss: 2650, unmet: 6800, curtail: 9800 },
  { scenario: "Industrial Peak", cap: 57520, op: 318900, loss: 3200, unmet: 15400, curtail: 3200 },
  { scenario: "Extreme Weather", cap: 57520, op: 39100, loss: 1200, unmet: 28600, curtail: 1100 },
  { scenario: "100% Electrification", cap: 78500, op: 345200, loss: 4100, unmet: 12800, curtail: 6200 },
]

export function WeightsSimulationPage() {
  const [method, setMethod] = useState<"entropy" | "equal" | "custom">("entropy")

  // Objective weight states (defaulting to paper's Shannon Entropy results)
  const [wCap, setWCap] = useState(0.023)
  const [wOp, setWOp] = useState(0.119)
  const [wLoss, setWLoss] = useState(0.023)
  const [wUnmet, setWUnmet] = useState(0.473)
  const [wCurtail, setWCurtail] = useState(0.362)

  // Interactive Live Fitness Function Simulator Inputs
  const [simCap, setSimCap] = useState(57520)
  const [simOp, setSimOp] = useState(273444)
  const [simLoss, setSimLoss] = useState(2763)
  const [simUnmet, setSimUnmet] = useState(3070)
  const [simCurtail, setSimCurtail] = useState(11932)
  const [oversizePenalty, setOversizePenalty] = useState(0.0)

  // Normalization constants (from objective_function.py)
  const NORM_C_CAPITAL = 80000.0
  const NORM_C_OP = 400000.0
  const NORM_LOSS = 5000.0
  const NORM_UNMET = 10000.0
  const NORM_CURTAIL = 10000.0

  // Calculate normalized terms
  const normCap = simCap / NORM_C_CAPITAL
  const normOp = simOp / NORM_C_OP
  const normLoss = simLoss / NORM_LOSS
  const normUnmet = simUnmet / NORM_UNMET
  const normCurtail = simCurtail / NORM_CURTAIL + oversizePenalty

  // Active weights based on method
  const activeWeights =
    method === "equal"
      ? { cap: 0.2, op: 0.2, loss: 0.2, unmet: 0.2, curtail: 0.2 }
      : method === "entropy"
        ? { cap: 0.0228, op: 0.1191, loss: 0.0226, unmet: 0.4733, curtail: 0.3622 }
        : { cap: wCap, op: wOp, loss: wLoss, unmet: wUnmet, curtail: wCurtail }

  // Total Fitness Evaluation
  const termCap = activeWeights.cap * normCap
  const termOp = activeWeights.op * normOp
  const termLoss = activeWeights.loss * normLoss
  const termUnmet = activeWeights.unmet * normUnmet
  const termCurtail = activeWeights.curtail * normCurtail

  const totalFitness = termCap + termOp + termLoss + termUnmet + termCurtail

  // Shannon Entropy Step Derivations
  const criteria = [
    {
      key: "cap",
      name: "Capital Cost (CapEx)",
      unit: "₹/day",
      weight: activeWeights.cap,
      entropy: 0.992,
      divergence: 0.008,
      desc: "Amortized equipment deployment. Low cross-scenario variance yields smaller weight.",
      color: "bg-[#D97706]",
      textColor: "text-[#D97706]",
    },
    {
      key: "op",
      name: "Operational Cost (OpEx)",
      unit: "₹/day",
      weight: activeWeights.op,
      entropy: 0.958,
      divergence: 0.042,
      desc: "Grid import purchases and fuel dispatch expenses across hours.",
      color: "bg-[#10B981]",
      textColor: "text-[#10B981]",
    },
    {
      key: "loss",
      name: "Transmission Losses",
      unit: "kWh",
      weight: activeWeights.loss,
      entropy: 0.992,
      divergence: 0.008,
      desc: "I²R resistive cable and hop losses in the IEEE 33-bus radial feeder.",
      color: "bg-[#606C38]",
      textColor: "text-[#606C38]",
    },
    {
      key: "unmet",
      name: "Unmet Load Deficit",
      unit: "kWh",
      weight: activeWeights.unmet,
      entropy: 0.834,
      divergence: 0.166,
      desc: "Blackout / deficit penalty. Extremely high variance (0 to 28,600 kWh) makes it highest priority!",
      color: "bg-[#DC2626]",
      textColor: "text-[#DC2626]",
    },
    {
      key: "curtail",
      name: "Renewable Curtailment",
      unit: "kWh",
      weight: activeWeights.curtail,
      entropy: 0.873,
      divergence: 0.127,
      desc: "Wasted solar & wind capacity. Penalizes over-generation during mid-day solar peaks.",
      color: "bg-[#8B5CF6]",
      textColor: "text-[#8B5CF6]",
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-xs font-bold uppercase tracking-wider text-copper">Page 04 · Analytical Modeling</div>
          <Heading level={1} className="mt-1">
            Weights & Fitness Function Simulation
          </Heading>
          <p className="mt-1 max-w-2xl text-xs text-forest-muted">
            Explore how data-driven Shannon Entropy calculates multi-objective criteria weights across 10 stress
            scenarios, and simulate the exact scalar fitness function in real time.
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            size="xs"
            variant={method === "entropy" ? "primary" : "outline"}
            onClick={() => setMethod("entropy")}
          >
            Shannon Entropy (Recommended)
          </Button>
          <Button
            size="xs"
            variant={method === "equal" ? "primary" : "outline"}
            onClick={() => setMethod("equal")}
          >
            Equal Heuristic (20% each)
          </Button>
          <Button
            size="xs"
            variant={method === "custom" ? "primary" : "outline"}
            onClick={() => setMethod("custom")}
          >
            Custom Weights
          </Button>
        </div>
      </div>

      {/* 1. Shannon Entropy Derivation & Weight Allocation */}
      <Card className="p-4 sm:p-6">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3 border-b border-olive/20 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-copper" />
              <Heading level={2}>Shannon Entropy Weight Derivation</Heading>
            </div>
            <p className="mt-1 text-xs text-forest-muted">
              Weights are computed directly from the information dispersion across all 10 scenarios. Greater variance
              yields higher information divergence (d_j), awarding critical reliability criteria higher priority.
            </p>
          </div>
          <Badge tone={method === "entropy" ? "olive" : "neutral"}>
            Sum of Weights: {(Object.values(activeWeights).reduce((a, b) => a + b, 0) * 100).toFixed(1)}%
          </Badge>
        </div>

        {/* Weights Bar Chart */}
        <div className="space-y-3">
          <div className="flex h-6 w-full overflow-hidden rounded-xl border border-olive/30 bg-cornsilk shadow-inner">
            {criteria.map((c) => (
              <div
                key={c.key}
                style={{ width: `${c.weight * 100}%` }}
                className={`${c.color} flex items-center justify-center transition-all duration-500`}
                title={`${c.name}: ${(c.weight * 100).toFixed(1)}%`}
              >
                {c.weight > 0.05 && (
                  <span className="truncate text-[10px] font-bold text-white">
                    {(c.weight * 100).toFixed(1)}%
                  </span>
                )}
              </div>
            ))}
          </div>

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
            {criteria.map((c) => (
              <div key={c.key} className="rounded-xl border border-olive/20 bg-cornsilk-soft p-3">
                <div className="flex items-center gap-1.5">
                  <span className={`h-2.5 w-2.5 rounded-full ${c.color}`} />
                  <span className="truncate font-sans text-xs font-bold text-forest">{c.name}</span>
                </div>
                <div className="mt-2 font-display text-xl font-bold text-forest">
                  {(c.weight * 100).toFixed(1)}%
                </div>
                <div className="mt-1 flex justify-between text-[10px] text-forest-muted">
                  <span>Entropy (E_j):</span>
                  <span className="font-mono">{c.entropy.toFixed(3)}</span>
                </div>
                <div className="flex justify-between text-[10px] text-forest-muted">
                  <span>Divergence (d_j):</span>
                  <span className="font-mono">{c.divergence.toFixed(3)}</span>
                </div>
                <p className="mt-2 text-[10px] leading-tight text-forest-muted">{c.desc}</p>
                {method === "custom" && (
                  <div className="mt-3 border-t border-olive/20 pt-2">
                    <input
                      type="range"
                      min="0.01"
                      max="0.80"
                      step="0.01"
                      value={c.weight}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value)
                        if (c.key === "cap") setWCap(val)
                        if (c.key === "op") setWOp(val)
                        if (c.key === "loss") setWLoss(val)
                        if (c.key === "unmet") setWUnmet(val)
                        if (c.key === "curtail") setWCurtail(val)
                      }}
                      className="w-full accent-copper"
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Mathematical Derivation Steps Table */}
        <div className="mt-6 overflow-x-auto rounded-xl border border-olive/20 bg-cornsilk/50 p-4">
          <div className="mb-2 font-display text-xs font-bold uppercase tracking-wider text-copper">
            Mathematical Formulation
          </div>
          <div className="grid gap-3 text-xs md:grid-cols-4">
            <div className="rounded-lg border border-olive/15 bg-cornsilk-card p-2.5">
              <span className="font-bold text-forest">1. Column Normalization:</span>
              <p className="mt-1 font-mono text-[11px] text-forest-muted">P_ij = x_ij / Σ(x_kj)</p>
              <span className="text-[10px] text-forest-muted">Standardizes scales across rupees, kW, and kWh</span>
            </div>
            <div className="rounded-lg border border-olive/15 bg-cornsilk-card p-2.5">
              <span className="font-bold text-forest">2. Information Entropy:</span>
              <p className="mt-1 font-mono text-[11px] text-forest-muted">E_j = -1/ln(10) * Σ P_ij * ln(P_ij)</p>
              <span className="text-[10px] text-forest-muted">Measures uniformity across 10 operational scenarios</span>
            </div>
            <div className="rounded-lg border border-olive/15 bg-cornsilk-card p-2.5">
              <span className="font-bold text-forest">3. Information Divergence:</span>
              <p className="mt-1 font-mono text-[11px] text-forest-muted">d_j = 1 - E_j</p>
              <span className="text-[10px] text-forest-muted">Highlights high-variance critical parameters</span>
            </div>
            <div className="rounded-lg border border-olive/15 bg-cornsilk-card p-2.5">
              <span className="font-bold text-forest">4. Objective Weight:</span>
              <p className="mt-1 font-mono text-[11px] text-forest-muted">W_j = d_j / Σ(d_k)</p>
              <span className="text-[10px] text-forest-muted">Normalized weight vector summing to 1.0</span>
            </div>
          </div>
        </div>
      </Card>

      {/* 2. Interactive Fitness Function In a Box */}
      <div className="rounded-2xl border-2 border-forest/40 bg-forest p-6 text-cornsilk shadow-2xl">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b border-cornsilk/15 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <Calculator className="h-5 w-5 text-caramel" />
              <h3 className="font-display text-xl font-bold text-cornsilk">
                Scalar Fitness Function Evaluation (In-a-Box)
              </h3>
            </div>
            <p className="mt-1 text-xs text-cornsilk/75">
              Real-time evaluation engine executing the exact multi-objective formula utilized by ABC and PSO.
            </p>
          </div>
          <div className="rounded-xl border border-caramel/50 bg-caramel/15 px-4 py-2 text-right">
            <div className="text-[10px] font-bold uppercase tracking-wider text-caramel">Computed Fitness (F)</div>
            <div className="font-display text-2xl font-bold text-cornsilk">{totalFitness.toFixed(4)}</div>
          </div>
        </div>

        {/* Formula Representation Box */}
        <div className="mb-6 rounded-xl border border-cornsilk/20 bg-forest-mid/70 p-4 font-mono text-xs">
          <div className="text-[10px] font-bold uppercase tracking-wider text-caramel mb-1.5 font-sans">
            Mathematical Objective Formula
          </div>
          <div className="leading-relaxed text-cornsilk/95">
            <span className="font-bold text-caramel">F(X)</span> ={" "}
            <span className="text-amber-400">W_cap</span> × (C_cap / 80k) +{" "}
            <span className="text-emerald-400">W_op</span> × (C_op / 400k) +{" "}
            <span className="text-lime-400">W_loss</span> × (Loss / 5k) +{" "}
            <span className="text-red-400 font-bold">W_unmet</span> × (Unmet / 10k) +{" "}
            <span className="text-purple-400">W_curtail</span> × (Curtail / 10k + P_oversize)
          </div>
          <div className="mt-3 border-t border-cornsilk/10 pt-2 text-[11px] text-cornsilk/70 font-sans flex flex-wrap gap-4">
            <span>Norm Constants: Cap: ₹80,000</span>
            <span>Op: ₹400,000</span>
            <span>Loss: 5,000 kWh</span>
            <span>Unmet: 10,000 kWh</span>
            <span>Curtail: 10,000 kWh</span>
          </div>
        </div>

        {/* Interactive Sliders Grid */}
        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {/* CapEx Slider */}
          <div className="rounded-xl border border-cornsilk/15 bg-forest-mid/50 p-3.5">
            <div className="flex justify-between text-xs font-semibold">
              <span className="text-amber-400">Daily CapEx (C_cap)</span>
              <span>₹{formatNumber(simCap)}</span>
            </div>
            <input
              type="range"
              min="0"
              max="80000"
              step="1000"
              value={simCap}
              onChange={(e) => setSimCap(Number(e.target.value))}
              className="mt-2 w-full accent-amber-400"
            />
            <div className="mt-2 flex justify-between text-[11px] text-cornsilk/60 font-mono">
              <span>Term: {activeWeights.cap.toFixed(3)} × {normCap.toFixed(2)}</span>
              <span className="text-amber-300 font-bold">+{termCap.toFixed(4)}</span>
            </div>
          </div>

          {/* OpEx Slider */}
          <div className="rounded-xl border border-cornsilk/15 bg-forest-mid/50 p-3.5">
            <div className="flex justify-between text-xs font-semibold">
              <span className="text-emerald-400">Daily OpEx (C_op)</span>
              <span>₹{formatNumber(simOp)}</span>
            </div>
            <input
              type="range"
              min="0"
              max="400000"
              step="5000"
              value={simOp}
              onChange={(e) => setSimOp(Number(e.target.value))}
              className="mt-2 w-full accent-emerald-400"
            />
            <div className="mt-2 flex justify-between text-[11px] text-cornsilk/60 font-mono">
              <span>Term: {activeWeights.op.toFixed(3)} × {normOp.toFixed(2)}</span>
              <span className="text-emerald-300 font-bold">+{termOp.toFixed(4)}</span>
            </div>
          </div>

          {/* Transmission Loss Slider */}
          <div className="rounded-xl border border-cornsilk/15 bg-forest-mid/50 p-3.5">
            <div className="flex justify-between text-xs font-semibold">
              <span className="text-lime-400">Cable Losses</span>
              <span>{formatNumber(simLoss)} kWh</span>
            </div>
            <input
              type="range"
              min="0"
              max="5000"
              step="100"
              value={simLoss}
              onChange={(e) => setSimLoss(Number(e.target.value))}
              className="mt-2 w-full accent-lime-400"
            />
            <div className="mt-2 flex justify-between text-[11px] text-cornsilk/60 font-mono">
              <span>Term: {activeWeights.loss.toFixed(3)} × {normLoss.toFixed(2)}</span>
              <span className="text-lime-300 font-bold">+{termLoss.toFixed(4)}</span>
            </div>
          </div>

          {/* Unmet Load Deficit Slider (High Penalty) */}
          <div className="rounded-xl border border-red-500/40 bg-red-950/20 p-3.5">
            <div className="flex justify-between text-xs font-semibold">
              <span className="text-red-400">Unmet Load Deficit</span>
              <span className="text-red-300 font-bold">{formatNumber(simUnmet)} kWh</span>
            </div>
            <input
              type="range"
              min="0"
              max="20000"
              step="250"
              value={simUnmet}
              onChange={(e) => setSimUnmet(Number(e.target.value))}
              className="mt-2 w-full accent-red-500"
            />
            <div className="mt-2 flex justify-between text-[11px] text-cornsilk/60 font-mono">
              <span>Term: {activeWeights.unmet.toFixed(3)} × {normUnmet.toFixed(2)}</span>
              <span className="text-red-400 font-bold">+{termUnmet.toFixed(4)}</span>
            </div>
          </div>

          {/* Renewable Curtailment Slider */}
          <div className="rounded-xl border border-cornsilk/15 bg-forest-mid/50 p-3.5">
            <div className="flex justify-between text-xs font-semibold">
              <span className="text-purple-400">Renewable Curtailment</span>
              <span>{formatNumber(simCurtail)} kWh</span>
            </div>
            <input
              type="range"
              min="0"
              max="25000"
              step="500"
              value={simCurtail}
              onChange={(e) => setSimCurtail(Number(e.target.value))}
              className="mt-2 w-full accent-purple-400"
            />
            <div className="mt-2 flex justify-between text-[11px] text-cornsilk/60 font-mono">
              <span>Term: {activeWeights.curtail.toFixed(3)} × {normCurtail.toFixed(2)}</span>
              <span className="text-purple-300 font-bold">+{termCurtail.toFixed(4)}</span>
            </div>
          </div>

          {/* Quick Preset Buttons */}
          <div className="flex flex-col justify-between rounded-xl border border-caramel/30 bg-forest-mid/60 p-3.5 text-xs">
            <div>
              <span className="font-semibold text-caramel">Test Evaluation Presets:</span>
              <p className="mt-1 text-[11px] text-cornsilk/70">
                Instantly load standard scenario vectors to see how fitness behaves.
              </p>
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              <Button
                size="xs"
                variant="outline"
                className="!text-cornsilk border-cornsilk/30"
                onClick={() => {
                  setSimCap(57520)
                  setSimOp(273444)
                  setSimLoss(2763)
                  setSimUnmet(3070)
                  setSimCurtail(11932)
                }}
              >
                Normal Preset
              </Button>
              <Button
                size="xs"
                variant="outline"
                className="!text-cornsilk border-cornsilk/30"
                onClick={() => {
                  setSimCap(68000)
                  setSimOp(198000)
                  setSimLoss(2100)
                  setSimUnmet(0) // 100% Demand satisfied
                  setSimCurtail(5200)
                }}
              >
                Zero-Deficit Expanded Preset
              </Button>
            </div>
          </div>
        </div>

        {/* Step-by-Step Cumulative Bar */}
        <div className="mt-6 rounded-xl border border-cornsilk/15 bg-forest-mid/40 p-4">
          <div className="mb-2 flex justify-between text-xs font-semibold">
            <span>Scalar Fitness Contribution Breakdown</span>
            <span className="font-mono text-caramel">F = {totalFitness.toFixed(4)}</span>
          </div>
          <div className="flex h-5 w-full overflow-hidden rounded-lg bg-forest/80 border border-cornsilk/20">
            <div style={{ width: `${(termCap / totalFitness) * 100}%` }} className="bg-amber-500" title={`CapEx: ${termCap.toFixed(4)}`} />
            <div style={{ width: `${(termOp / totalFitness) * 100}%` }} className="bg-emerald-500" title={`OpEx: ${termOp.toFixed(4)}`} />
            <div style={{ width: `${(termLoss / totalFitness) * 100}%` }} className="bg-lime-500" title={`Loss: ${termLoss.toFixed(4)}`} />
            <div style={{ width: `${(termUnmet / totalFitness) * 100}%` }} className="bg-red-500" title={`Unmet Deficit: ${termUnmet.toFixed(4)}`} />
            <div style={{ width: `${(termCurtail / totalFitness) * 100}%` }} className="bg-purple-500" title={`Curtailment: ${termCurtail.toFixed(4)}`} />
          </div>
          <div className="mt-2 flex flex-wrap justify-between text-[10px] text-cornsilk/70">
            <span className="text-amber-400">CapEx: {(termCap / totalFitness * 100).toFixed(1)}%</span>
            <span className="text-emerald-400">OpEx: {(termOp / totalFitness * 100).toFixed(1)}%</span>
            <span className="text-lime-400">Loss: {(termLoss / totalFitness * 100).toFixed(1)}%</span>
            <span className="text-red-400 font-bold">Unmet Deficit: {(termUnmet / totalFitness * 100).toFixed(1)}%</span>
            <span className="text-purple-400">Curtailment: {(termCurtail / totalFitness * 100).toFixed(1)}%</span>
          </div>
        </div>
      </div>
    </div>
  )
}
