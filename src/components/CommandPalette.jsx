import React, { useEffect, useState } from 'react';
import { Command } from 'cmdk';

export default function CommandPalette({ projects }) {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const down = (e) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, []);

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
      <Command className="w-full max-w-xl bg-cyber-card border border-cyber-border rounded-xl overflow-hidden shadow-2xl">
        <Command.Input placeholder="Search projects, alternatives... (Ctrl+K)" className="w-full p-4 bg-transparent border-b border-cyber-border outline-none text-white font-mono" />
        <Command.List className="max-h-96 overflow-y-auto p-2">
          <Command.Empty className="p-4 text-gray-500 font-mono">No results found.</Command.Empty>
          <Command.Group heading="Projects">
            {projects.map((p) => (
              <Command.Item key={p.id} onSelect={() => window.location.href = `/project/${p.id}`} className="p-3 text-white hover:bg-white/10 rounded cursor-pointer font-mono flex justify-between">
                <span>{p.name}</span>
                <span className="text-xs text-cyber-neonRed">{p.riskLevel}</span>
              </Command.Item>
            ))}
          </Command.Group>
        </Command.List>
      </Command>
    </div>
  );
}