export function calculateRollingAverage(data: { time: string; value: number }[], windowSize: number): { time: string; value: number | null }[] {
  if (!data || data.length === 0) {
    return [];
  }

  const smoothedData: { time: string; value: number | null }[] = [];

  for (let i = 0; i < data.length; i++) {
    const start = Math.max(0, i - Math.floor(windowSize / 2));
    const end = Math.min(data.length, i + Math.ceil(windowSize / 2));
    const window = data.slice(start, end);
    
    if (window.length > 0) {
      const sum = window.reduce((acc, val) => acc + val.value, 0);
      smoothedData.push({ time: data[i].time, value: sum / window.length });
    } else {
      smoothedData.push({ time: data[i].time, value: null });
    }
  }

  return smoothedData;
}