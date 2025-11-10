"use client";

import {
  Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart, Bar, Cell
} from 'recharts';
import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { calculateRollingAverage } from '@/utils/smoothing';

// Define the structure of our data props
interface SleepData {
  metadata: {
    startTime: string;
    endTime: string;
    totalAwakeTimeMinutes: number;
  };
  sleepStages: {
    level: string;
    startTime: string;
    endTime: string;
    durationSeconds: number;
  }[];
  heartRate: {
    time: string;
    value: number;
  }[];
  restingHeartRate?: number;
}

interface SmoothedHeartRate {
  time: string;
  value: number | null;
}

const sleepStageMapping = {
  wake: { level: 4, color: '#c084fc' },   // light purple
  light: { level: 3, color: '#a855f7' },    // medium purple
  rem: { level: 2, color: '#7c3aed' },  // deeper purple
  deep: { level: 1, color: '#5b21b6' },   // dark purple
};

type SleepStage = keyof typeof sleepStageMapping;

interface CustomTickProps {
  x: number;
  y: number;
  payload: {
    value: number;
  };
}

const CustomYAxisTick = ({ x, y, payload }: CustomTickProps) => {
  const stage = Object.keys(sleepStageMapping).find(
    (key) => sleepStageMapping[key as SleepStage].level === payload.value
  ) as SleepStage | undefined;

  const color = stage ? sleepStageMapping[stage].color : '#FFFFFF'; // Default to white if not found
  const formattedStage = stage ? stage.toUpperCase() : '';

  return (
    <g transform={`translate(${x},${y})`}>
      <text x={1} y={4} textAnchor="start" fill={color} fontSize={12}>
        {formattedStage}
      </text>
    </g>
  );
};

export default function SleepChart({ data }: { data: SleepData }) {
  const smoothedHeartRate = useMemo(() => {
    if (!data || !data.heartRate) {
      return [];
    }
    return calculateRollingAverage(data.heartRate, 9);
  }, [data]);

  const chartData = useMemo(() => {
    if (!data || !data.sleepStages || !smoothedHeartRate) {
      return [];
    }

    const combinedData: { time: number; heartRate?: number; sleepStage?: number; sleepColor?: string, restingHeartRate?: number }[] = smoothedHeartRate.map(hr => ({
      time: new Date(hr.time).getTime(),
      heartRate: hr.value ?? undefined,
      restingHeartRate: data.restingHeartRate,
    }));

    const timeToDataMap = new Map(combinedData.map(d => [d.time, d]));

    data.sleepStages.forEach(stage => {
      const stageInfo = sleepStageMapping[stage.level as SleepStage];
      if (!stageInfo) return;

      const startTime = new Date(stage.startTime).getTime();
      const endTime = new Date(stage.endTime).getTime();

      // Iterate through the heart rate data points and assign sleep stage if within range
      for (let i = 0; i < combinedData.length; i++) {
        const dataPoint = combinedData[i];
        if (dataPoint.time >= startTime && dataPoint.time < endTime) {
          dataPoint.sleepStage = stageInfo.level;
          dataPoint.sleepColor = stageInfo.color;
        }
      }
    });

    return combinedData;
  }, [data]);

  const maxHeartRate = useMemo(() => {
    if (!smoothedHeartRate || smoothedHeartRate.length === 0) {
      return 100; // Default max if no data
    }
    const validValues = smoothedHeartRate.map(hr => hr.value).filter(v => v !== null) as number[];
    if (validValues.length === 0) {
      return 100;
    }
    return Math.max(...validValues);
  }, [smoothedHeartRate]);

  const xAxisTicks = useMemo(() => {
    if (!chartData.length) {
      return [];
    }
    const startTime = chartData[0].time;
    const endTime = chartData[chartData.length - 1].time;
    const ticks = [];
    let currentTick = new Date(startTime);
    currentTick.setMinutes(Math.ceil(currentTick.getMinutes() / 15) * 15, 0, 0);

    while (currentTick.getTime() <= endTime) {
      ticks.push(currentTick.getTime());
      currentTick.setMinutes(currentTick.getMinutes() + 15);
    }
    return ticks;
  }, [chartData]);

  if (!chartData.length) {
    return <p>No data available to display chart.</p>;
  }

  const yAxisTickFormatter = (value: number) => {
    console.log('yAxisTickFormatter - value:', value);
    const stage = Object.keys(sleepStageMapping).find(key => sleepStageMapping[key as SleepStage].level === value);
    const formattedStage = stage ? stage.toUpperCase() : '';
    console.log('yAxisTickFormatter - formattedStage:', formattedStage);
    return formattedStage;
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const time = new Date(label).toLocaleString();
      const heartRate = payload.find((p: any) => p.dataKey === 'heartRate')?.value;
      const restingHeartRate = payload.find((p: any) => p.dataKey === 'restingHeartRate')?.value;
      const sleepStageLevel = payload.find((p: any) => p.dataKey === 'sleepStage')?.value;
      const sleepStage = yAxisTickFormatter(sleepStageLevel);

      return (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-gray-900 text-gray-100 p-3 border border-gray-600 rounded-lg shadow-2xl backdrop-blur-sm"
        >
          <p className="font-semibold text-sm">{`${time}`}</p>
          {heartRate && <p className="text-orange-400 text-xs mt-1">{`Heart Rate: ${Math.round(heartRate)} bpm`}</p>}
          {restingHeartRate && <p className="text-white text-xs">{`Resting: ${Math.round(restingHeartRate)} bpm`}</p>}
          {sleepStage && <p className="text-purple-300 text-xs">{`Sleep: ${sleepStage}`}</p>}
        </motion.div>
      );
    }
    return null;
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="w-full bg-gradient-to-br from-gray-900 to-black p-6 rounded-lg"
    >
      <ResponsiveContainer width="100%" height={400}>
        <ComposedChart
          data={chartData}
          margin={{ top: 20, right: 20, left: 20, bottom: 5 }}
        >
          <defs>
            <linearGradient id="heartRateGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ff7f0e" stopOpacity={0.8}/>
              <stop offset="95%" stopColor="#ff7f0e" stopOpacity={0.5}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis
            dataKey="time"
            type="number"
            domain={['dataMin', 'dataMax']}
            tickFormatter={(unixTime) => new Date(unixTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            scale="time"
            ticks={xAxisTicks}
            stroke="#666"
          />
          <YAxis
            yAxisId="left"
            orientation="left"
            stroke="#ff7f0e"
            label={{ value: 'Heart Rate (bpm)', angle: -90, position: 'insideLeft' }}
            domain={[45, maxHeartRate + 5]}
            tickFormatter={(value) => String(Math.round(value))}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            stroke="#8884d8"
            type="number"
            domain={[0.5, 4.5]}
            ticks={[1, 2, 3, 4]}
            tickCount={4}
            tickFormatter={yAxisTickFormatter}
            tick={(props) => <CustomYAxisTick {...props} />}
            label={{ value: 'Sleep Stage', angle: 90, position: 'insideRight' , offset: -15 }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend 
            wrapperStyle={{ paddingTop: '20px' }} 
            formatter={(value) => {
              if (value === 'sleepStage') {
                return '';
              }
              if (value === 'Resting Heart Rate' && data.restingHeartRate !== undefined) {
                return `${value} (${Math.round(data.restingHeartRate)} bpm)`;
              }
              return value;
            }}
          />

          <Bar yAxisId="right" dataKey="sleepStage" barSize={20} radius={[2, 2, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.sleepColor || 'transparent'} />
            ))}
          </Bar>

          <Line
            yAxisId="left"
            type="monotone"
            dataKey="heartRate"
            stroke="url(#heartRateGradient)"
            strokeWidth={3.0}
            dot={false}
            name="Heart Rate"
            isAnimationActive={true}
          />
          
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="restingHeartRate"
            stroke="#FFFFFF"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={false}
            name="Resting Heart Rate"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </motion.div>
  );
}
