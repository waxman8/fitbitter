"use client";

import {
  Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ComposedChart, Bar, Cell
} from 'recharts';
import { useMemo } from 'react';

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
}

const sleepStageMapping = {
  wake: { level: 4, color: '#facc15' }, // yellow-400
  rem: { level: 3, color: '#8b5cf6' },  // violet-500
  light: { level: 2, color: '#3b82f6' }, // blue-500
  deep: { level: 1, color: '#1f2937' }, // gray-800
};

type SleepStage = keyof typeof sleepStageMapping;

export default function SleepChart({ data }: { data: SleepData }) {
  const chartData = useMemo(() => {
    if (!data || !data.sleepStages || !data.heartRate) {
      return [];
    }

    const combinedData: { time: number; heartRate?: number; sleepStage?: number; sleepColor?: string }[] = data.heartRate.map(hr => ({
      time: new Date(hr.time).getTime(),
      heartRate: hr.value,
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
      const sleepStageLevel = payload.find((p: any) => p.dataKey === 'sleepStage')?.value;
      const sleepStage = yAxisTickFormatter(sleepStageLevel);

      return (
        <div className="bg-white p-2 border border-gray-300 rounded shadow-lg">
          <p className="label">{`${time}`}</p>
          {heartRate && <p className="intro">{`Heart Rate: ${heartRate} bpm`}</p>}
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
        />
        <YAxis
          yAxisId="left"
          orientation="left"
          stroke="#ef4444"
          label={{ value: 'Heart Rate (bpm)', angle: -90, position: 'insideLeft' }}
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
          stroke="#ef4444" // red-500
          dot={false}
          name="Heart Rate"
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}