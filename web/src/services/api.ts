/**
 * api.ts - Typed API Client for EcoGridAI FastAPI Backend
 */

export type ResourceType = "solar" | "wind" | "battery" | "grid"

export interface InstalledResource {
  type: ResourceType
  label: string
  rating_kw: number
}

export interface BusTopology {
  id: number
  loadKw: number
  x: number
  y: number
  resources: ResourceType[]
  installed: InstalledResource[]
  loss_factor: number
  loss_pct: number
  distance_hops: number
  connected_buses: number[]
}

export interface NetworkResponse {
  system_name: string
  voltage_kv: number
  root_bus: number
  total_buses: number
  total_branches: number
  total_base_load_kw: number
  buses: BusTopology[]
  branches: [number, number][]
  loss_model: {
    formula: string
    base_loss_factor: number
    loss_per_hop: number
    max_loss_factor: number
  }
  pv_buses: number[]
  wind_buses: number[]
  grid_bus: number
}

export interface BackendScenario {
  index: number
  name: string
  description: string
  load_multiplier: number
  solar_multiplier: number
  wind_multiplier: number
  grid_available: boolean
  battery_available: boolean
  load: number
  solar: number
  wind: number
  grid: number
  battery: number
}

export interface DatasetItem {
  id: string
  name: string
  description?: string
  hours?: number
  peak_load_kw?: number
  total_pv_kw?: number
  total_wind_kw?: number
  pv_buses?: number[]
  wind_buses?: number[]
  is_default?: boolean
  error?: string
}

export interface ValidationSummary {
  peak_kw?: number
  min_kw?: number
  total_kwh?: number
  avg_kw?: number
  load_factor?: number
  hours?: number
}

export interface ValidationResult {
  valid: boolean
  errors: string[]
  warnings: string[]
  summary?: ValidationSummary | null
}

export interface Config {
  solarKw: number
  windKw: number
  batteryKw: number
  batteryKwh: number
  gridLimitKw: number
}

export interface HourResult {
  hour: number
  demand: number
  solar: number
  wind: number
  battery: number
  grid: number
  unmet: number
  soc: number
  curtailment?: number
}

export interface AlgorithmResult {
  name: "ABC" | "PSO"
  dispatch: HourResult[]
  unmetKwh: number
  cost: number
  capitalCost: number
  operationalCost: number
  energyLossKwh: number
  busTransLossKwh: number
  curtailmentKwh: number
  renewableUtilization: number
  loadSatisfaction: number
  objective: number
  executionSeconds: number
  convergenceIterations: number
  convergence: number[]
  vector?: number[]
  capacities?: {
    pv_bus13_kw: number
    pv_bus30_kw: number
    wind_bus6_kw: number
    battery_power_kw: number
    battery_capacity_kwh: number
    grid_limit_kw: number
  }
}

export interface RecommendationItem {
  action: string
  category: string
  priority: "RECOMMENDED" | "ALTERNATIVE" | "EXPENSIVE"
  additional_capacity: string
  additional_capacity_kw?: number
  additional_capacity_kwh?: number
  capital_cost: number
  daily_amortized_cost: number
  cost_effectiveness_phi: number
  description: string
}

export interface OptimizationResponse {
  scenario: BackendScenario
  dataset: string
  config: Config
  abc: AlgorithmResult
  pso: AlgorithmResult
  overallWinner: "ABC" | "PSO"
  losses: {
    abc_system_loss_kwh: number
    pso_system_loss_kwh: number
    abc_cable_transmission_loss_kwh: number
    pso_cable_transmission_loss_kwh: number
    cable_loss_details?: Record<string, number>
  }
  feasibility: string
  violations: {
    battery_violations: number
    thermal_violations: number
    prohibited_violations: number
  }
  recommendations: RecommendationItem[]
  completedAt: string
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api"

async function apiRequest<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`
  const response = await fetch(url, {
    ...options,
    headers: {
      Accept: "application/json",
      ...options?.headers,
    },
  })

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status}: ${response.statusText}`
    try {
      const errJson = await response.json()
      if (errJson.detail) {
        errorDetail = typeof errJson.detail === "string" ? errJson.detail : JSON.stringify(errJson.detail)
      } else if (errJson.message) {
        errorDetail = errJson.message
      }
    } catch {
      // response wasn't JSON
    }
    throw new Error(errorDetail)
  }

  return response.json()
}

export const api = {
  getHealth: () => apiRequest<{ status: string; models: string[] }>("/health"),

  getNetwork: () => apiRequest<NetworkResponse>("/network"),

  getDatasets: () => apiRequest<DatasetItem[]>("/datasets"),

  getScenarios: () => apiRequest<BackendScenario[]>("/scenarios"),

  getBenchmark: () => apiRequest<any[]>("/benchmark"),

  validateDataset: async (params: { file?: File; raw_csv?: string }): Promise<ValidationResult> => {
    if (params.file) {
      const formData = new FormData()
      formData.append("file", params.file)
      return apiRequest<ValidationResult>("/datasets/validate", {
        method: "POST",
        body: formData,
      })
    }
    return apiRequest<ValidationResult>("/datasets/validate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ csv_content: params.raw_csv }),
    })
  },

  runOptimization: async (params: {
    dataset: string
    scenario_index: number
    config: Config
    modifications?: Record<number, ResourceType[]>
    max_iter?: number
    use_entropy_weights?: boolean
    custom_load_profile?: number[]
  }): Promise<OptimizationResponse> => {
    const stringModifications: Record<string, string[]> = {}
    if (params.modifications) {
      for (const [bus, types] of Object.entries(params.modifications)) {
        stringModifications[bus] = types
      }
    }

    return apiRequest<OptimizationResponse>("/optimize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        dataset: params.dataset,
        scenario_index: params.scenario_index,
        config: params.config,
        modifications: stringModifications,
        max_iter: params.max_iter ?? 60,
        use_entropy_weights: params.use_entropy_weights ?? true,
        async_job: false,
        custom_load_profile: params.custom_load_profile,
      }),
    })
  },

  getRecommendations: async (params: {
    scenario_index: number
    unmet_kwh: number
    peak_gap_kw: number
    load_satisfaction: number
    grid_available: boolean
  }): Promise<{ recommendations: RecommendationItem[] }> => {
    return apiRequest("/recommendations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    })
  },

  addBus: async (params: { id: number; loadKw: number; type: string; connect_to: number }) => {
    return apiRequest<{ status: string; bus: any; branch: [number, number] }>("/network/add-bus", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    })
  },

  deleteBus: async (params: { id: number }) => {
    return apiRequest<{ status: string; deleted_id: number }>("/network/delete-bus", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    })
  },

  addBranch: async (params: { from_bus: number; to_bus: number }) => {
    return apiRequest<{ status: string; branch: [number, number] }>("/network/add-branch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    })
  },

  deleteBranch: async (params: { from_bus: number; to_bus: number }) => {
    return apiRequest<{ status: string; branch: [number, number] }>("/network/delete-branch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(params),
    })
  },
}
