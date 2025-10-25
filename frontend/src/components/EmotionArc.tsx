import React, { useState, useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { AudioFeatures } from '../types';

interface EmotionArcProps {
    features: AudioFeatures;
    width?: number;
    height?: number;
}

const EmotionArc: React.FC<EmotionArcProps> = ({
    features,
    width = 400,
    height = 200
}) => {
    const svgRef = useRef<SVGSVGElement>(null);

    useEffect(() => {
        if (!svgRef.current || !features) return;

        const svg = d3.select(svgRef.current);
        svg.selectAll('*').remove(); // Clear previous content

        const margin = { top: 20, right: 30, bottom: 40, left: 40 };
        const innerWidth = width - margin.left - margin.right;
        const innerHeight = height - margin.top - margin.bottom;

        // Create scales
        const xScale = d3.scaleLinear()
            .domain([0, features.duration])
            .range([0, innerWidth]);

        const energyScale = d3.scaleLinear()
            .domain([0, Math.max(...features.energy_curve.values)])
            .range([innerHeight, 0]);

        const pitchScale = d3.scaleLinear()
            .domain([0, Math.max(...features.f0_curve.values.filter(v => v > 0))])
            .range([innerHeight, 0]);

        // Create line generators
        const energyLine = d3.line<number>()
            .x((d, i) => xScale(features.energy_curve.time[i]))
            .y(d => energyScale(d))
            .curve(d3.curveMonotoneX);

        const pitchLine = d3.line<number>()
            .x((d, i) => xScale(features.f0_curve.time[i]))
            .y(d => pitchScale(d))
            .curve(d3.curveMonotoneX);

        // Create main group
        const g = svg.append('g')
            .attr('transform', `translate(${margin.left},${margin.top})`);

        // Add grid lines
        g.append('g')
            .attr('class', 'grid')
            .attr('transform', `translate(0,${innerHeight})`)
            .call(d3.axisBottom(xScale)
                .tickSize(-innerHeight)
                .tickFormat(() => '')
            )
            .style('stroke', '#374151')
            .style('opacity', 0.3);

        // Add axes
        g.append('g')
            .attr('transform', `translate(0,${innerHeight})`)
            .call(d3.axisBottom(xScale)
                .tickFormat(d3.format('.1f'))
            )
            .style('color', '#9CA3AF');

        g.append('g')
            .call(d3.axisLeft(energyScale)
                .tickFormat(d3.format('.2f'))
            )
            .style('color', '#9CA3AF');

        // Add axis labels
        g.append('text')
            .attr('transform', `translate(${innerWidth / 2}, ${innerHeight + 35})`)
            .style('text-anchor', 'middle')
            .style('fill', '#9CA3AF')
            .style('font-size', '12px')
            .text('Time (seconds)');

        g.append('text')
            .attr('transform', 'rotate(-90)')
            .attr('y', 0 - margin.left)
            .attr('x', 0 - (innerHeight / 2))
            .attr('dy', '1em')
            .style('text-anchor', 'middle')
            .style('fill', '#9CA3AF')
            .style('font-size', '12px')
            .text('Amplitude');

        // Add energy curve
        g.append('path')
            .datum(features.energy_curve.values)
            .attr('fill', 'none')
            .attr('stroke', '#0ea5e9')
            .attr('stroke-width', 2)
            .attr('d', energyLine);

        // Add pitch curve (only for voiced segments)
        const voicedPitchValues = features.f0_curve.values.map((v, i) =>
            features.f0_curve.confidence[i] > 0.5 ? v : 0
        );

        g.append('path')
            .datum(voicedPitchValues)
            .attr('fill', 'none')
            .attr('stroke', '#a855f7')
            .attr('stroke-width', 2)
            .attr('opacity', 0.7)
            .attr('d', pitchLine);

        // Add legend
        const legend = g.append('g')
            .attr('transform', `translate(${innerWidth - 120}, 20)`);

        legend.append('rect')
            .attr('width', 12)
            .attr('height', 12)
            .attr('fill', '#0ea5e9');

        legend.append('text')
            .attr('x', 18)
            .attr('y', 9)
            .style('fill', '#9CA3AF')
            .style('font-size', '12px')
            .text('Energy');

        legend.append('rect')
            .attr('y', 20)
            .attr('width', 12)
            .attr('height', 12)
            .attr('fill', '#a855f7');

        legend.append('text')
            .attr('x', 18)
            .attr('y', 29)
            .style('fill', '#9CA3AF')
            .style('font-size', '12px')
            .text('Pitch');

        // Add pause markers
        features.pause_timestamps.forEach(pauseTime => {
            g.append('line')
                .attr('x1', xScale(pauseTime))
                .attr('x2', xScale(pauseTime))
                .attr('y1', 0)
                .attr('y2', innerHeight)
                .attr('stroke', '#ef4444')
                .attr('stroke-width', 1)
                .attr('opacity', 0.6)
                .attr('stroke-dasharray', '3,3');
        });

    }, [features, width, height]);

    return (
        <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-100">Emotion Arc</h3>
            <div className="bg-gray-800 rounded-lg p-4">
                <svg
                    ref={svgRef}
                    width={width}
                    height={height}
                    className="w-full h-auto"
                />
            </div>
            <div className="text-sm text-gray-400">
                <p>Blue line: Energy level (RMS amplitude)</p>
                <p>Purple line: Pitch (fundamental frequency)</p>
                <p>Red dashed lines: Pause markers</p>
            </div>
        </div>
    );
};

export default EmotionArc;
