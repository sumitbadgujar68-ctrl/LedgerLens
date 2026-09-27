export const formatEther = (wei: string | number | null | undefined): string => {
  if (wei === null || wei === undefined) return '—';
  const num = typeof wei === 'string' ? parseFloat(wei) : wei;
  if (isNaN(num)) return '—';
  const eth = num / 1e18;
  return eth.toFixed(4);
};

export const formatAmount = (amount: string | number | null | undefined, decimals = 18): string => {
  if (amount === null || amount === undefined) return '—';
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  if (isNaN(num)) return '—';
  const formatted = num / Math.pow(10, decimals);
  return formatted.toFixed(4);
};

export const formatBlockNumber = (block: string | number | null | undefined): string => {
  if (block === null || block === undefined) return '—';
  const num = typeof block === 'string' ? parseInt(block, 10) : block;
  if (isNaN(num)) return '—';
  return `#${num.toLocaleString()}`;
};

export const formatGas = (gas: string | number | null | undefined): string => {
  if (gas === null || gas === undefined) return '—';
  const num = typeof gas === 'string' ? parseInt(gas, 10) : gas;
  if (isNaN(num)) return '—';
  return `${num.toLocaleString()} Gwei`;
};

export const formatTimestamp = (ts: string | null | undefined): string => {
  if (!ts) return '—';
  try {
    return new Date(ts).toLocaleString();
  } catch {
    return '—';
  }
};

export const formatUsd = (amount: string | number | null | undefined): string => {
  if (amount === null || amount === undefined) return '—';
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  if (isNaN(num)) return '—';
  return `$${num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};