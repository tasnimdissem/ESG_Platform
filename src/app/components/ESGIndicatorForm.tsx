import React from 'react';
import { DEFAULT_INDICATORS, ESGIndicators, INDICATOR_CATEGORIES, INDICATOR_LABELS } from '../utils/esgIndicators';

type ESGFormProps = {
  data: ESGIndicators;
  onChange: (field: keyof ESGIndicators, value: string | number) => void;
  submitLabel?: string;
  onSubmit: (e: React.FormEvent) => void;
  isLoading?: boolean;
  onCancel?: () => void;
};

export function ESGIndicatorForm({ data, onChange, submitLabel = 'Calculer', onSubmit, isLoading, onCancel }: ESGFormProps) {
  const handleChange = (field: keyof ESGIndicators, value: any) => {
    onChange(field, value);
  };

  const renderInput = (field: keyof ESGIndicators, value: any) => {
    const isNumeric = typeof DEFAULT_INDICATORS[field] === 'number';
    return (
      <div key={field}>
        <label className="block text-sm font-medium text-slate-700 mb-1">{INDICATOR_LABELS[field] || field}</label>
        <input
          type={isNumeric ? 'number' : 'text'}
          step={isNumeric ? '0.1' : undefined}
          value={value}
          onChange={(e) => handleChange(field, isNumeric ? parseFloat(e.target.value) || 0 : e.target.value)}
          className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
        />
      </div>
    );
  };

  return (
    <form onSubmit={onSubmit} className="space-y-6">
      {Object.entries(INDICATOR_CATEGORIES).map(([category, fields]) => (
        <div key={category}>
          <h3 className="text-lg font-semibold text-slate-800 mb-3">{category}</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {fields.map((field) => renderInput(field as keyof ESGIndicators, data[field as keyof ESGIndicators]))}
          </div>
        </div>
      ))}

      <div className="flex gap-2 pt-4">
        <button type="submit" disabled={isLoading} className="bg-emerald-600 text-white px-4 py-2 rounded-md disabled:opacity-50">
          {isLoading ? 'Calcul en cours...' : submitLabel}
        </button>
        {onCancel && (
          <button type="button" onClick={onCancel} className="px-4 py-2 border border-slate-300 rounded-md hover:bg-slate-50">
            Annuler
          </button>
        )}
      </div>
    </form>
  );
}
