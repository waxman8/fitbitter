"use client";

import React from 'react';
import DatePicker from 'react-datepicker';
import "react-datepicker/dist/react-datepicker.css";
import { DateField, Label } from 'react-aria-components';

interface DateTimePickerProps {
  label: string;
  selected: Date;
  onChange: (date: Date | null) => void;
}

export default function DateTimePicker({ label, selected, onChange }: DateTimePickerProps) {
  return (
    <div className="flex flex-col">
      <Label className="mb-1 text-sm font-medium text-gray-700">{label}</Label>
      <DatePicker
        selected={selected}
        onChange={onChange}
        showTimeSelect
        timeFormat="HH:mm"
        timeIntervals={15}
        dateFormat="MMMM d, yyyy HH:mm"
        className="w-full p-2 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500"
      />
    </div>
  );
}