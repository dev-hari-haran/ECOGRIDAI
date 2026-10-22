export type ResourceType = "solar" | "wind" | "battery" | "grid"

export interface BusData {
  id: number
  loadKw: number
  x: number
  y: number
  resources: ResourceType[]
}

export const branches: [number, number][] = [
  [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 8], [8, 9], [9, 10],
  [10, 11], [11, 12], [12, 13], [13, 14], [14, 15], [15, 16], [16, 17],
  [17, 18], [2, 19], [19, 20], [20, 21], [21, 22], [3, 23], [23, 24],
  [24, 25], [6, 26], [26, 27], [27, 28], [28, 29], [29, 30], [30, 31],
  [31, 32], [32, 33],
]

const loads = [
  0, 100, 90, 120, 60, 60, 200, 200, 60, 60, 45, 60, 60, 120, 60, 60, 60,
  90, 90, 90, 90, 90, 90, 420, 420, 60, 60, 60, 120, 200, 150, 210, 60,
]

const positions: [number, number][] = [
  [34, 100], [88, 100], [142, 100], [196, 100], [250, 100], [304, 100],
  [358, 100], [412, 100], [466, 100], [520, 100], [574, 100], [628, 100],
  [682, 100], [736, 100], [790, 100], [844, 100], [898, 100], [952, 100],
  [88, 174], [160, 174], [232, 174], [304, 174], [142, 30], [220, 30],
  [298, 30], [304, 248], [376, 248], [448, 248], [520, 248], [592, 248],
  [664, 248], [736, 248], [808, 248],
]

export const buses: BusData[] = positions.map(([x, y], index) => {
  const id = index + 1
  const resources: ResourceType[] = []
  if ([6, 18, 25].includes(id)) resources.push("solar")
  if ([14, 30].includes(id)) resources.push("wind")
  if ([11, 24, 32].includes(id)) resources.push("battery")
  if (id === 1) resources.push("grid")
  return { id, loadKw: loads[index], x, y, resources }
})

export const loadProfile = [
  0.62, 0.58, 0.55, 0.53, 0.55, 0.63, 0.76, 0.86, 0.92, 0.88, 0.84, 0.82,
  0.8, 0.82, 0.85, 0.9, 0.96, 1, 0.98, 0.93, 0.87, 0.8, 0.72, 0.66,
]
export const solarProfile = [
  0, 0, 0, 0, 0, 0.04, 0.16, 0.35, 0.57, 0.76, 0.9, 0.98, 1, 0.92, 0.77,
  0.55, 0.3, 0.1, 0, 0, 0, 0, 0, 0,
]
export const windProfile = [
  0.62, 0.58, 0.55, 0.51, 0.49, 0.5, 0.55, 0.62, 0.67, 0.65, 0.59, 0.54,
  0.5, 0.48, 0.52, 0.61, 0.7, 0.79, 0.85, 0.88, 0.84, 0.77, 0.71, 0.66,
]

export interface Scenario {
  name: string
  description: string
  load: number
  solar: number
  wind: number
  grid: number
  battery: number
}

export const scenarios: Scenario[] = [
  { name: "Normal Operation", description: "Nominal demand and resource availability", load: 1, solar: 1, wind: 1, grid: 1, battery: 1 },
  { name: "Peak Summer", description: "High cooling demand with strong solar", load: 1.25, solar: 1.15, wind: 0.8, grid: 1, battery: 1 },
  { name: "Battery Failure", description: "Storage unavailable for dispatch", load: 1, solar: 1, wind: 1, grid: 1, battery: 0 },
  { name: "Grid Outage", description: "Islanded system with no grid import", load: 0.9, solar: 1, wind: 1, grid: 0, battery: 1 },
  { name: "Low Renewable", description: "Cloud cover and weak wind conditions", load: 1, solar: 0.25, wind: 0.3, grid: 1, battery: 1 },
  { name: "High Renewable Surplus", description: "Strong generation and moderate demand", load: 0.8, solar: 1.35, wind: 1.25, grid: 1, battery: 1 },
  { name: "Night Peak", description: "Elevated evening and overnight demand", load: 1.15, solar: 0.7, wind: 1, grid: 1, battery: 1 },
  { name: "Partial Wind Failure", description: "Reduced wind fleet availability", load: 1, solar: 1, wind: 0.35, grid: 1, battery: 1 },
  { name: "Partial PV Failure", description: "Reduced photovoltaic availability", load: 1, solar: 0.4, wind: 1, grid: 1, battery: 1 },
  { name: "Extreme Stress", description: "Peak demand with constrained supply", load: 1.35, solar: 0.25, wind: 0.3, grid: 0.55, battery: 0.5 },
]

export const totalBaseLoadKw = buses.reduce((sum, bus) => sum + bus.loadKw, 0)
