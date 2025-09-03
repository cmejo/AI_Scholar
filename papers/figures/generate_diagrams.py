#!/usr/bin/env python3
"""
Generate technical diagrams for AI Scholar academic paper
Creates publication-quality figures using matplotlib and other visualization libraries
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import seaborn as sns
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import networkx as nx
from matplotlib.patches import Rectangle, Circle, Arrow
import pandas as pd

# Set publication-quality style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")
plt.rcParams.update({
    'font.size': 12,
    'font.family': 'serif',
    'figure.figsize': (10, 8),
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'axes.linewidth': 1.5,
    'grid.alpha': 0.3
})

def create_system_architecture():
    """Create high-level system architecture diagram"""
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Define components and their positions
    components = {
        'User Interface': (2, 8, 3, 1.5),
        'VR/AR Interface': (6, 8, 3, 1.5),
        'API Gateway': (4, 6, 2, 1),
        'Multi-Modal AI Engine': (1, 4, 3, 1.5),
        'Knowledge Graph Service': (5, 4, 3, 1.5),
        'Blockchain Layer': (9, 4, 3, 1.5),
        'Collaboration Engine': (1, 2, 3, 1.5),
        'Translation Service': (5, 2, 3, 1.5),
        'Global Infrastructure': (9, 2, 3, 1.5),
        'Database Cluster': (2, 0.5, 2, 1),
        'Vector Database': (5, 0.5, 2, 1),
        'Blockchain Network': (8, 0.5, 2, 1)
    }
    
    # Color scheme for different layers
    colors = {
        'User Interface': '#3498db',
        'VR/AR Interface': '#9b59b6',
        'API Gateway': '#e74c3c',
        'Multi-Modal AI Engine': '#2ecc71',
        'Knowledge Graph Service': '#f39c12',
        'Blockchain Layer': '#34495e',
        'Collaboration Engine': '#1abc9c',
        'Translation Service': '#e67e22',
        'Global Infrastructure': '#95a5a6',
        'Database Cluster': '#16a085',
        'Vector Database': '#27ae60',
        'Blockchain Network': '#2c3e50'
    }
    
    # Draw components
    for name, (x, y, w, h) in components.items():
        rect = FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0.1",
            facecolor=colors[name],
            edgecolor='black',
            alpha=0.8,
            linewidth=1.5
        )
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, name, ha='center', va='center', 
                fontsize=10, fontweight='bold', color='white')
    
    # Draw connections
    connections = [
        ('User Interface', 'API Gateway'),
        ('VR/AR Interface', 'API Gateway'),
        ('API Gateway', 'Multi-Modal AI Engine'),
        ('API Gateway', 'Knowledge Graph Service'),
        ('API Gateway', 'Blockchain Layer'),
        ('Multi-Modal AI Engine', 'Collaboration Engine'),
        ('Knowledge Graph Service', 'Translation Service'),
        ('Blockchain Layer', 'Global Infrastructure'),
        ('Collaboration Engine', 'Database Cluster'),
        ('Translation Service', 'Vector Database'),
        ('Global Infrastructure', 'Blockchain Network')
    ]
    
    for start, end in connections:
        start_pos = components[start]
        end_pos = components[end]
        
        start_center = (start_pos[0] + start_pos[2]/2, start_pos[1])
        end_center = (end_pos[0] + end_pos[2]/2, end_pos[1] + end_pos[3])
        
        ax.annotate('', xy=end_center, xytext=start_center,
                   arrowprops=dict(arrowstyle='->', lw=2, color='gray'))
    
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 10)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('AI Scholar System Architecture', fontsize=16, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig('papers/figures/system_architecture.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_multimodal_architecture():
    """Create multi-modal AI architecture diagram"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Input modalities
    inputs = ['Text', 'Images', 'Equations', 'Tables', 'Citations']
    input_colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6']
    
    # Draw input layer
    for i, (inp, color) in enumerate(zip(inputs, input_colors)):
        rect = Rectangle((i*2, 6), 1.5, 1, facecolor=color, alpha=0.7)
        ax.add_patch(rect)
        ax.text(i*2 + 0.75, 6.5, inp, ha='center', va='center', fontweight='bold')
    
    # Encoder layer
    for i in range(5):
        rect = Rectangle((i*2, 4), 1.5, 1, facecolor='lightblue', alpha=0.7)
        ax.add_patch(rect)
        ax.text(i*2 + 0.75, 4.5, f'Encoder\n{i+1}', ha='center', va='center', fontsize=9)
        
        # Arrows from input to encoder
        ax.arrow(i*2 + 0.75, 6, 0, -0.8, head_width=0.1, head_length=0.1, fc='black', ec='black')
    
    # Fusion layer
    fusion_rect = Rectangle((2, 2), 6, 1, facecolor='orange', alpha=0.7)
    ax.add_patch(fusion_rect)
    ax.text(5, 2.5, 'Multi-Modal Fusion Layer\n(Cross-Attention)', ha='center', va='center', fontweight='bold')
    
    # Arrows from encoders to fusion
    for i in range(5):
        ax.arrow(i*2 + 0.75, 4, (5 - (i*2 + 0.75))*0.3, -0.8, 
                head_width=0.1, head_length=0.1, fc='gray', ec='gray')
    
    # Output layer
    outputs = ['Research\nUnderstanding', 'Gap\nIdentification', 'Proposal\nGeneration']
    output_positions = [1, 5, 9]
    
    for i, (out, pos) in enumerate(zip(outputs, output_positions)):
        rect = Rectangle((pos-1, 0), 2, 1, facecolor='lightgreen', alpha=0.7)
        ax.add_patch(rect)
        ax.text(pos, 0.5, out, ha='center', va='center', fontweight='bold', fontsize=9)
        
        # Arrow from fusion to output
        ax.arrow(5, 2, pos-5, -0.8, head_width=0.1, head_length=0.1, fc='green', ec='green')
    
    ax.set_xlim(-0.5, 10.5)
    ax.set_ylim(-0.5, 7.5)
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title('Multi-Modal AI Architecture', fontsize=16, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig('papers/figures/multimodal_architecture.png', dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    create_system_architecture()
    create_multimodal_architecture()
    print("Generated system architecture and multi-modal architecture diagrams")