"use client";

import {
  Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart, Bar, Cell
} from 'recharts';
import { useMemo } from 'react';
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
  wake: { level: 4, color: '#ffdd57' }, // brighter, pastel yellow
  rem: { level: 3, color: '#9b59b6' },  // a soft purple
  light: { level: 2, color: '#3498db' }, // a gentle blue
  deep: { level: 1, color: '#2ecc71' }, // a calm green
};

type SleepStage = keyof typeof sleepStageMapping;

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
    const stage = Object.keys(sleepStageMapping).find(key => sleepStageMapping[key as SleepStage].level === value);
    return stage ? stage.toUpperCase() : '';
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const time = new Date(label).toLocaleString();
      const heartRate = payload.find((p: any) => p.dataKey === 'heartRate')?.value;
      const restingHeartRate = payload.find((p: any) => p.dataKey === 'restingHeartRate')?.value;
      const sleepStageLevel = payload.find((p: any) => p.dataKey === 'sleepStage')?.value;
      const sleepStage = yAxisTickFormatter(sleepStageLevel);

      return (
        <div className="bg-gray-800 text-gray-200 p-2 border border-gray-600 rounded shadow-lg">
          <p className="label font-semibold">{`${time}`}</p>
          {heartRate && <p className="intro">{`Heart Rate: ${Math.round(heartRate)} bpm`}</p>}
          {restingHeartRate && <p className="intro">{`Resting Heart Rate: ${Math.round(restingHeartRate)} bpm`}</p>}
          {sleepStage && <p className="intro">{`Sleep Stage: ${sleepStage}`}</p>}
        </div>
      );
    }
    return null;
  };

  return (
    <ResponsiveContainer width="100%" height={400}>
      <ComposedChart
        data={chartData}
        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="time"
          type="number"
          domain={['dataMin', 'dataMax']}
          tickFormatter={(unixTime) => new Date(unixTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          scale="time"
          ticks={xAxisTicks}
        />
        <YAxis
          yAxisId="left"
          orientation="left"
          stroke="#ef4444"
          label={{ value: 'Heart Rate (bpm)', angle: -90, position: 'insideLeft' }}
          domain={[40, maxHeartRate + 5]}
          tickFormatter={(value) => String(Math.round(value))}
        />
        <YAxis
          yAxisId="right"
          orientation="right"
          stroke="#8884d8"
          type="number"
          domain={[0.5, 4.5]}
          ticks={[1, 2, 3, 4]}
          tickFormatter={yAxisTickFormatter}
          label={{ value: 'Sleep Stage', angle: 90, position: 'insideRight' }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend />

        <Bar yAxisId="right" dataKey="sleepStage" barSize={20} >
          {chartData.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.sleepColor || 'transparent'} />
          ))}
        </Bar>

        <Line
          yAxisId="left"
          type="monotone"
          dataKey="heartRate"
          stroke="#ff7f0e" // a vibrant orange
          dot={false}
          name="Heart Rate"
        />
        
        <Line
          yAxisId="left"
          type="monotone"
          dataKey="restingHeartRate"
          stroke="#FFFFFF"
          strokeWidth={2}
          dot={false}
          name="Resting Heart Rate"
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}