// Generated from results_real_entropy.json
export const benchmarkData = [
  {
    "scenario_name": "Normal Operation",
    "scenario_params": {
      "name": "Normal Operation",
      "load_multiplier": 1.0,
      "solar_multiplier": 1.0,
      "wind_multiplier": 1.0,
      "grid_available": true,
      "battery_available": true
    },
    "abc": {
      "vector": [
        1.0,
        1.0,
        1.0,
        0.9934195066626166,
        100.0,
        2000.0
      ],
      "fitness": 153499.98890938057,
      "capital_cost": 57520.0873560533,
      "c_capital": 57520.0873560533,
      "operational_cost": 273444.8182592378,
      "c_op": 273444.8182592378,
      "total_cost": 330964.9056152911,
      "energy_loss_kwh": 2763.495923344259,
      "energy_loss": 2763.495923344259,
      "bus_trans_loss": 1820.7811880000013,
      "unmet_load_kwh": 3069.9860224666877,
      "curtailment_kwh": 11932.392326413385,
      "renewable_utilization": 71.4009435868994,
      "load_satisfaction": 93.8728207700373,
      "convergence_iterations": 9,
      "computational_time": 1.350841999053955
    },
    "pso": {
      "vector": [
        1.0,
        1.0,
        1.0,
        0.0,
        100.0,
        2000.0
      ],
      "fitness": 153748.34169289612,
      "capital_cost": 57512.14,
      "c_capital": 57512.14,
      "operational_cost": 273499.56560825,
      "c_op": 273499.56560825,
      "total_cost": 331011.70560825,
      "energy_loss_kwh": 2761.370005600001,
      "energy_loss": 2761.370005600001,
      "bus_trans_loss": 1820.7811880000013,
      "unmet_load_kwh": 3074.9531200000006,
      "curtailment_kwh": 11945.306779999995,
      "renewable_utilization": 71.36999076733359,
      "load_satisfaction": 93.8629072731625,
      "convergence_iterations": 4,
      "computational_time": 0.44582605361938477
    },
    "abc_weights": [
      0.022809104997183232,
      0.11907837278387012,
      0.022564571910202922,
      0.4733445256178823,
      0.3622034246908614
    ],
    "pso_weights": [
      0.02965037753729777,
      0.11881272416853354,
      0.0221052017186883,
      0.47331891654600966,
      0.3561127800294707
    ],
    "weight_method": "shannon_entropy"
  },
  {
    "scenario_name": "Peak Summer",
    "scenario_params": {
      "name": "Peak Summer",
      "load_multiplier": 1.3,
      "solar_multiplier": 1.1,
      "wind_multiplier": 1.0,
      "grid_available": true,
      "battery_available": true
    },
    "abc": {
      "vector": [
        1.0,
        1.0,
        1.0,
        0.9993162494191301,
        137.32520728155293,
        2000.0
      ],
      "fitness": 489176.6387461772,
      "capital_cost": 57594.78494455846,
      "c_capital": 57594.78494455846,
      "operational_cost": 324880.07893664343,
      "c_op": 324880.07893664343,
      "total_cost": 382474.8638812019,
      "energy_loss_kwh": 3211.2519977499323,
      "energy_loss": 3211.2519977499323,
      "bus_trans_loss": 2104.248037000002,
      "unmet_load_kwh": 9783.515530004646,
      "curtailment_kwh": 7496.338321256387,
      "renewable_utilization": 82.27422042785318,
      "load_satisfaction": 84.97979802544533,
      "convergence_iterations": 26,
      "computational_time": 1.455118179321289
    },
    "pso": {
      "vector": [
        1.0,
        1.0,
        1.0,
        0.0,
        100.0,
        2000.0
      ],
      "fitness": 489576.36582094873,
      "capital_cost": 57512.14,
      "c_capital": 57512.14,
      "operational_cost": 324922.634819125,
      "c_op": 324922.634819125,
      "total_cost": 382434.774819125,
      "energy_loss_kwh": 3211.1320798000024,
      "energy_loss": 3211.1320798000024,
      "bus_trans_loss": 2104.248037000002,
      "unmet_load_kwh": 9791.51006,
      "curtailment_kwh": 7507.330799999997,
      "renewable_utilization": 82.2482277035643,
      "load_satisfaction": 84.96752437443986,
      "convergence_iterations": 5,
      "computational_time": 0.4443933963775635
    },
    "abc_weights": [
      0.022809104997183232,
      0.11907837278387012,
      0.022564571910202922,
      0.4733445256178823,
      0.3622034246908614
    ],
    "pso_weights": [
      0.02965037753729777,
      0.11881272416853354,
      0.0221052017186883,
      0.47331891654600966,
      0.3561127800294707
    ],
    "weight_method": "shannon_entropy"
  },
  {
    "scenario_name": "Battery Failure",
    "scenario_params": {
      "name": "Battery Failure",
      "load_multiplier": 1.0,
      "solar_multiplier": 1.0,
      "wind_multiplier": 1.0,
      "grid_available": true,
      "battery_available": false
    },
    "abc": {
      "vector": [
        1.0,
        1.0,
        1.0,
        0.0,
        0.0,
        2000.0
      ],
      "fitness": 154708.3444363423,
      "capital_cost": 57312.14,
      "c_capital": 57312.14,
      "operational_cost": 273499.56560825,
      "c_op": 273499.56560825,
      "total_cost": 330811.70560825,
      "energy_loss_kwh": 2761.370005600001,
      "energy_loss": 2761.370005600001,
      "bus_trans_loss": 1820.7811880000013,
      "unmet_load_kwh": 3074.9531200000006,
      "curtailment_kwh": 11945.306779999995,
      "renewable_utilization": 71.36999076733359,
      "load_satisfaction": 93.8629072731625,
      "convergence_iterations": 6,
      "computational_time": 0.9692647457122803
    },
    "pso": {
      "vector": [
        1.0,
        1.0,
        1.0,
        0.0,
        0.0,
        2000.0
      ],
      "fitness": 154708.34161877018,
      "capital_cost": 57312.14,
      "c_capital": 57312.14,
      "operational_cost": 273499.56560825,
      "c_op": 273499.56560825,
      "total_cost": 330811.70560825,
      "energy_loss_kwh": 2761.370005600001,
      "energy_loss": 2761.370005600001,
      "bus_trans_loss": 1820.7811880000013,
      "unmet_load_kwh": 3074.9531200000006,
      "curtailment_kwh": 11945.306779999995,
      "renewable_utilization": 71.36999076733359,
      "load_satisfaction": 93.8629072731625,
      "convergence_iterations": 3,
      "computational_time": 0.4201812744140625
    },
    "abc_weights": [
      0.022809104997183232,
      0.11907837278387012,
      0.022564571910202922,
      0.4733445256178823,
      0.3622034246908614
    ],
    "pso_weights": [
      0.02965037753729777,
      0.11881272416853354,
      0.0221052017186883,
      0.47331891654600966,
      0.3561127800294707
    ],
    "weight_method": "shannon_entropy"
  },
  {
    "scenario_name": "Grid Outage",
    "scenario_params": {
      "name": "Grid Outage",
      "load_multiplier": 1.0,
      "solar_multiplier": 1.0,
      "wind_multiplier": 1.0,
      "grid_available": false,
      "battery_available": true
    },
    "abc": {
      "vector": [
        1.0,
        1.0,
        1.0,
        0.9997238324611157,
        100.0,
        695.7413234421364
      ],
      "fitness": 1015785.2265605697,
      "capital_cost": 55520.13779065969,
      "c_capital": 55520.13779065969,
      "operational_cost": 57441.81183335251,
      "c_op": 57441.81183335251,
      "total_cost": 112961.9496240122,
      "energy_loss_kwh": 2418.5949890613633,
      "energy_loss": 2418.5949890613633,
      "bus_trans_loss": 1820.7811880000013,
      "unmet_load_kwh": 20315.675777842927,
      "curtailment_kwh": 11932.310370178002,
      "renewable_utilization": 71.40114001615976,
      "load_satisfaction": 59.45330507770849,
      "convergence_iterations": 16,
      "computational_time": 1.4700922966003418
    },
    "pso": {
      "vector": [
        1.0,
        1.0,
        1.0,
        0.0,
        100.0,
        264.1759587257207
      ],
      "fitness": 1016335.0728007731,
      "capital_cost": 55512.14,
      "c_capital": 55512.14,
      "operational_cost": 57421.77736774999,
      "c_op": 57421.77736774999,
      "total_cost": 112933.91736775,
      "energy_loss_kwh": 2416.3356132000013,
      "energy_loss": 2416.3356132000013,
      "bus_trans_loss": 1820.7811880000013,
      "unmet_load_kwh": 20326.67274,
      "curtailment_kwh": 11945.306779999995,
      "renewable_utilization": 71.36999076733359,
      "load_satisfaction": 59.431356978391946,
      "convergence_iterations": 4,
      "computational_time": 0.4313931465148926
    },
    "abc_weights": [
      0.022809104997183232,
      0.11907837278387012,
      0.022564571910202922,
      0.4733445256178823,
      0.3622034246908614
    ],
    "pso_weights": [
      0.02965037753729777,
      0.11881272416853354,
      0.0221052017186883,
      0.47331891654600966,
      0.3561127800294707
    ],
    "weight_method": "shannon_entropy"
  },
  {
    "scenario_name": "Low Renewable",
    "scenario_params": {
      "name": "Low Renewable",
      "load_multiplier": 1.0,
      "solar_multiplier": 0.4,
      "wind_multiplier": 0.3,
      "grid_available": true,
      "battery_available": true
    },
    "abc": {
      "vector": [
        1.0,
        1.0,
        1.0,
        0.997787295367341,
        100.0,
        2000.0
      ],
      "fitness": 386012.6025067585,
      "capital_cost": 57520.12229836294,
      "c_capital": 57520.12229836294,
      "operational_cost": 392116.627897982,
      "c_op": 392116.627897982,
      "total_cost": 449636.750196345,
      "energy_loss_kwh": 1634.1861115713905,
      "energy_loss": 1634.1861115713905,
      "bus_trans_loss": 786.9820081000006,
      "unmet_load_kwh": 7720.241931341694,
      "curtailment_kwh": 0.0,
      "renewable_utilization": 100.0,
      "load_satisfaction": 84.59168684618422,
      "convergence_iterations": 15,
      "computational_time": 1.599447250366211
    },
    "pso": {
      "vector": [
        1.0,
        1.0,
        1.0,
        0.0,
        100.0,
        2000.0
      ],
      "fitness": 386461.61175138736,
      "capital_cost": 57512.14,
      "c_capital": 57512.14,
      "operational_cost": 392284.0915287001,
      "c_op": 392284.0915287001,
      "total_cost": 449796.2315287001,
      "energy_loss_kwh": 1634.4854477600006,
      "energy_loss": 1634.4854477600006,
      "bus_trans_loss": 786.9820081000006,
      "unmet_load_kwh": 7729.222017,
      "curtailment_kwh": 0.0,
      "renewable_utilization": 100.0,
      "load_satisfaction": 84.57376409542046,
      "convergence_iterations": 5,
      "computational_time": 0.459852933883667
    },
    "abc_weights": [
      0.022809104997183232,
      0.11907837278387012,
      0.022564571910202922,
      0.4733445256178823,
      0.3622034246908614
    ],
    "pso_weights": [
      0.02965037753729777,
      0.11881272416853354,
      0.0221052017186883,
      0.47331891654600966,
      0.3561127800294707
    ],
    "weight_method": "shannon_entropy"
  },
  {
    "scenario_name": "High Renewable Surplus",
    "scenario_params": {
      "name": "High Renewable Surplus",
      "load_multiplier": 1.0,
      "solar_multiplier": 1.5,
      "wind_multiplier": 1.4,
      "grid_available": true,
      "battery_available": true
    },
    "abc": {
      "vector": [
        0.0,
        0.42033810236264096,
        1.0,
        0.9947204929205185,
        100.0,
        2000.0
      ],
      "fitness": 76407.66796021874,
      "capital_cost": 34682.34857336826,
      "c_capital": 34682.34857336826,
      "operational_cost": 266664.6523817204,
      "c_op": 266664.6523817204,
      "total_cost": 301347.0009550887,
      "energy_loss_kwh": 2704.9806991425276,
      "energy_loss": 2704.9806991425276,
      "bus_trans_loss": 1731.4262979775363,
      "unmet_load_kwh": 1528.1354320283185,
      "curtailment_kwh": 19948.5856373664,
      "renewable_utilization": 62.0230539058769,
      "load_satisfaction": 96.95009696748689,
      "convergence_iterations": 17,
      "computational_time": 1.610307216644287
    },
    "pso": {
      "vector": [
        0.0,
        0.0,
        1.0,
        0.9999996764441353,
        100.0,
        2000.0
      ],
      "fitness": 76406.56005772672,
      "capital_cost": 27383.639997411552,
      "c_capital": 27383.639997411552,
      "operational_cost": 277504.8105810337,
      "c_op": 277504.8105810337,
      "total_cost": 304888.4505784453,
      "energy_loss_kwh": 2558.214012234063,
      "energy_loss": 2558.214012234063,
      "bus_trans_loss": 1584.6484192000014,
      "unmet_load_kwh": 1528.1143152942236,
      "curtailment_kwh": 18760.28037620622,
      "renewable_utilization": 62.82608507933575,
      "load_satisfaction": 96.95013911296039,
      "convergence_iterations": 3,
      "computational_time": 0.7272768020629883
    },
    "abc_weights": [
      0.022809104997183232,
      0.11907837278387012,
      0.022564571910202922,
      0.4733445256178823,
      0.3622034246908614
    ],
    "pso_weights": [
      0.02965037753729777,
      0.11881272416853354,
      0.0221052017186883,
      0.47331891654600966,
      0.3561127800294707
    ],
    "weight_method": "shannon_entropy"
  },
  {
    "scenario_name": "Night Peak",
    "scenario_params": {
      "name": "Night Peak",
      "load_multiplier": 1.2,
      "solar_multiplier": 0.0,
      "wind_multiplier": 1.0,
      "grid_available": true,
      "battery_available": true
    },
    "abc": {
      "vector": [
        0.0006911111265291382,
        0.0,
        1.0,
        0.998771289045706,
        100.0,
        2000.0
      ],
      "fitness": 407362.7089009733,
      "capital_cost": 27392.457387175957,
      "c_capital": 27392.457387175957,
      "operational_cost": 349027.0890813857,
      "c_op": 349027.0890813857,
      "total_cost": 376419.54646856163,
      "energy_loss_kwh": 2485.333795977344,
      "energy_loss": 2485.333795977344,
      "bus_trans_loss": 1445.892969500001,
      "unmet_load_kwh": 8147.238848398589,
      "curtailment_kwh": 7120.472208398587,
      "renewable_utilization": 80.24687521365885,
      "load_satisfaction": 86.44956027808894,
      "convergence_iterations": 19,
      "computational_time": 1.5682449340820312
    },
    "pso": {
      "vector": [
        0.0,
        0.0,
        1.0,
        0.0,
        100.0,
        2000.0
      ],
      "fitness": 407812.1542611323,
      "capital_cost": 27375.64,
      "c_capital": 27375.64,
      "operational_cost": 349082.131367125,
      "c_op": 349082.131367125,
      "total_cost": 376457.77136712504,
      "energy_loss_kwh": 2485.2738697000013,
      "energy_loss": 2485.2738697000013,
      "bus_trans_loss": 1445.892969500001,
      "unmet_load_kwh": 8156.227789999999,
      "curtailment_kwh": 7129.461149999997,
      "renewable_utilization": 80.22193870945617,
      "load_satisfaction": 86.43460992330002,
      "convergence_iterations": 4,
      "computational_time": 0.4149434566497803
    },
    "abc_weights": [
      0.022809104997183232,
      0.11907837278387012,
      0.022564571910202922,
      0.4733445256178823,
      0.3622034246908614
    ],
    "pso_weights": [
      0.02965037753729777,
      0.11881272416853354,
      0.0221052017186883,
      0.47331891654600966,
      0.3561127800294707
    ],
    "weight_method": "shannon_entropy"
  },
  {
    "scenario_name": "Partial Wind Failure",
    "scenario_params": {
      "name": "Partial Wind Failure",
      "load_multiplier": 1.0,
      "solar_multiplier": 1.0,
      "wind_multiplier": 0.2,
      "grid_available": true,
      "battery_available": true
    },
    "abc": {
      "vector": [
        1.0,
        1.0,
        1.0,
        0.9952100144076363,
        100.0,
        2000.0
      ],
      "fitness": 387515.8618689244,
      "capital_cost": 57520.10168011526,
      "c_capital": 57520.10168011526,
      "operational_cost": 390977.52813180146,
      "c_op": 390977.52813180146,
      "total_cost": 448497.62981191673,
      "energy_loss_kwh": 1822.7577429953903,
      "energy_loss": 1822.7577429953903,
      "bus_trans_loss": 976.1537054000008,
      "unmet_load_kwh": 7750.307079884737,
      "curtailment_kwh": 0.0,
      "renewable_utilization": 100.0,
      "load_satisfaction": 84.53168183236637,
      "convergence_iterations": 15,
      "computational_time": 1.436478853225708
    },
    "pso": {
      "vector": [
        1.0,
        1.0,
        1.0,
        0.0,
        100.0,
        2000.0
      ],
      "fitness": 387913.95077521715,
      "capital_cost": 57512.14,
      "c_capital": 57512.14,
      "operational_cost": 391157.02421000006,
      "c_op": 391157.02421000006,
      "total_cost": 448669.1642100001,
      "energy_loss_kwh": 1823.0762102000008,
      "energy_loss": 1823.0762102000008,
      "bus_trans_loss": 976.1537054000008,
      "unmet_load_kwh": 7758.268759999999,
      "curtailment_kwh": 0.0,
      "renewable_utilization": 100.0,
      "load_satisfaction": 84.51579164893202,
      "convergence_iterations": 5,
      "computational_time": 0.4782593250274658
    },
    "abc_weights": [
      0.022809104997183232,
      0.11907837278387012,
      0.022564571910202922,
      0.4733445256178823,
      0.3622034246908614
    ],
    "pso_weights": [
      0.02965037753729777,
      0.11881272416853354,
      0.0221052017186883,
      0.47331891654600966,
      0.3561127800294707
    ],
    "weight_method": "shannon_entropy"
  },
  {
    "scenario_name": "Partial PV Failure",
    "scenario_params": {
      "name": "Partial PV Failure",
      "load_multiplier": 1.0,
      "solar_multiplier": 0.2,
      "wind_multiplier": 1.0,
      "grid_available": true,
      "battery_available": true
    },
    "abc": {
      "vector": [
        1.0,
        1.0,
        1.0,
        0.9981427107631554,
        100.0,
        2000.0
      ],
      "fitness": 157516.93143061962,
      "capital_cost": 57520.125141686105,
      "c_capital": 57520.125141686105,
      "operational_cost": 298728.67211913253,
      "c_op": 298728.67211913253,
      "total_cost": 356248.79726081865,
      "energy_loss_kwh": 2386.5054703710775,
      "energy_loss": 2386.5054703710775,
      "bus_trans_loss": 1447.4241185000012,
      "unmet_load_kwh": 3150.3264064461846,
      "curtailment_kwh": 9549.582457470839,
      "renewable_utilization": 74.31697113763573,
      "load_satisfaction": 93.712474785253,
      "convergence_iterations": 10,
      "computational_time": 1.3821840286254883
    },
    "pso": {
      "vector": [
        1.0,
        1.0,
        1.0,
        0.0,
        100.0,
        2000.0
      ],
      "fitness": 157766.46646458015,
      "capital_cost": 57512.14,
      "c_capital": 57512.14,
      "operational_cost": 298796.181501375,
      "c_op": 298796.181501375,
      "total_cost": 356308.321501375,
      "energy_loss_kwh": 2386.405656100001,
      "energy_loss": 2386.405656100001,
      "bus_trans_loss": 1447.4241185000012,
      "unmet_load_kwh": 3155.3171200000006,
      "curtailment_kwh": 9561.560169999997,
      "renewable_utilization": 74.28475779867966,
      "load_satisfaction": 93.70251415474658,
      "convergence_iterations": 4,
      "computational_time": 0.4164469242095947
    },
    "abc_weights": [
      0.022809104997183232,
      0.11907837278387012,
      0.022564571910202922,
      0.4733445256178823,
      0.3622034246908614
    ],
    "pso_weights": [
      0.02965037753729777,
      0.11881272416853354,
      0.0221052017186883,
      0.47331891654600966,
      0.3561127800294707
    ],
    "weight_method": "shannon_entropy"
  },
  {
    "scenario_name": "Extreme Stress",
    "scenario_params": {
      "name": "Extreme Stress",
      "load_multiplier": 1.4,
      "solar_multiplier": 1.0,
      "wind_multiplier": 0.3,
      "grid_available": false,
      "battery_available": true
    },
    "abc": {
      "vector": [
        1.0,
        1.0,
        1.0,
        59.41496110817731,
        5000.0,
        1399.4142676214992
      ],
      "fitness": 2681614.9038923476,
      "capital_cost": 65787.45968886542,
      "c_capital": 65787.45968886542,
      "operational_cost": 30873.333131924996,
      "c_op": 30873.333131924996,
      "total_cost": 96660.79282079042,
      "energy_loss_kwh": 1486.1883813400007,
      "energy_loss": 1486.1883813400007,
      "bus_trans_loss": 1156.3903081000008,
      "unmet_load_kwh": 52231.24793799999,
      "curtailment_kwh": 0.0,
      "renewable_utilization": 100.0,
      "load_satisfaction": 25.539396322349354,
      "convergence_iterations": 17,
      "computational_time": 1.430992603302002
    },
    "pso": {
      "vector": [
        1.0,
        1.0,
        1.0,
        59.37502104111143,
        5000.0,
        457.975583946246
      ],
      "fitness": 2681614.909227298,
      "capital_cost": 65787.14016832889,
      "c_capital": 65787.14016832889,
      "operational_cost": 30873.333131924996,
      "c_op": 30873.333131924996,
      "total_cost": 96660.47330025389,
      "energy_loss_kwh": 1486.1883813400007,
      "energy_loss": 1486.1883813400007,
      "bus_trans_loss": 1156.3903081000008,
      "unmet_load_kwh": 52231.24793799999,
      "curtailment_kwh": 0.0,
      "renewable_utilization": 100.0,
      "load_satisfaction": 25.539396322349354,
      "convergence_iterations": 3,
      "computational_time": 0.7048478126525879
    },
    "abc_weights": [
      0.022809104997183232,
      0.11907837278387012,
      0.022564571910202922,
      0.4733445256178823,
      0.3622034246908614
    ],
    "pso_weights": [
      0.02965037753729777,
      0.11881272416853354,
      0.0221052017186883,
      0.47331891654600966,
      0.3561127800294707
    ],
    "weight_method": "shannon_entropy"
  }
] as const;
