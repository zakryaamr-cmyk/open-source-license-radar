import React from 'react';
import { motion } from 'framer-motion';

export default function TiltCard({ title, category, risk, description }) {
  return (
    <motion.div
      whileHover={{ scale: 1.02, rotateX: 5, rotateY: -5 }}
      transition={{ type: "spring", stiffness: 300 }}
      className="p-6 bg-cyber-card border border-cyber-border rounded-xl backdrop-blur-lg hover:border-cyber-neonBlue transition-all relative overflow-hidden group shadow-lg"
    >
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent group-hover:translate-x-full transition-transform duration-1000" />
      <div className="flex justify-between items-start mb-4">
        <span className="text-xs font-mono px-2 py-1 bg-white/5 rounded text-gray-400">{category}</span>
        <span className={`text-xs font-mono font-bold px-2 py-1 rounded ${risk === 'CRITICAL' ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
          {risk}
        </span>
      </div>
      <h3 className="text-xl font-mono font-bold text-white mb-2">{title}</h3>
      <p className="text-sm text-gray-400 font-sans">{description}</p>
    </motion.div>
  );
}