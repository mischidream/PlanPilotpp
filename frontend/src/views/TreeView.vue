<template>
  <div class="p-4">
    <h1 class="text-xl font-bold mb-4">Tree Visualization</h1>
    <div id="cy" style="width: 100%; height: 700px; border: 1px solid #ccc;"></div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";
import cytoscape from "cytoscape";
import testDataSolution from "@/testdata/example_answer_sets.json";
import type { Solution } from "@/models/Solution";

// Then use it instead of hardcoded `solutions`

const solutions = testDataSolution as Solution[];

interface PlanTreeNode {
  name: string;
  children: PlanTreeNode[];
  solutions: string[];
}

/* ---- Build merged tree from actions ---- */
function buildMergedTree(solutions: Solution[]): PlanTreeNode {
  const root: PlanTreeNode = { name: "ROOT", children: [], solutions: [] };

  for (const sol of solutions) {
    let current = root;

    for (const facet of sol.facets) {
      // Construct a label for the action
      const label = facet.constant2
        ? `${facet.action}(${facet.constant1},${facet.constant2})`
        : `${facet.action}(${facet.constant1})`;

      // Check if a child with the same label already exists
      let child = current.children.find((c) => c.name === label);

      if (!child) {
        child = { name: label, children: [], solutions: [] };
        current.children.push(child);
      }

      // Add solution label if not already present
      if (!child.solutions.includes(sol.label)) {
        child.solutions.push(sol.label);
      }

      current = child; // descend into child
    }
  }

  return root;
}

/* ---- Convert to Cytoscape format ---- */
function treeToCytoscapeElements(tree: any) {
  const elements: any[] = [];

  function traverse(node: any, parentId: string | null) {
    const nodeId = node.name === "ROOT" ? "root" : node.name + "-" + node.solutions.join("_");

    elements.push({
      data: {
        id: nodeId,
        label: node.name === "ROOT" ? "ROOT" : node.name,
        solutions: node.solutions.join(", "),
        sharedCount: node.solutions.length,
      },
    });

    if (parentId) {
      elements.push({ data: { source: parentId, target: nodeId } });
    }

    for (const child of node.children) {
      traverse(child, nodeId);
    }
  }

  traverse(tree, null);
  return elements;
}

/* ---- Initialize Cytoscape ---- */
onMounted(() => {
  const tree = buildMergedTree(solutions);
  const elements = treeToCytoscapeElements(tree);

  cytoscape({
    container: document.getElementById("cy")!,
    elements,
    layout: {
      name: "breadthfirst",
      directed: true,
      padding: 20,
      spacingFactor: 1.2,
    },
    style: [
      {
        selector: "node",
        style: {
          "background-color":  "#29b6f6",
          label: "data(label)",
          "shape": "round-rectangle",
          "text-valign": "center",
          "text-halign": "center",
          "font-size": "10px",
          "color": "#333",
          "width": "label",
          "height": "label",
          "padding": "5px",
          "border-color": "#555",
          "border-width": 1,
        },
      },
      {
        selector: "edge",
        style: {
          width: 2,
          "line-color": "#ccc",
          "target-arrow-shape": "triangle",
          "target-arrow-color": "#ccc",
          "curve-style": "bezier",
        },
      },
    ],
  });
});
</script>

<style>
body {
  font-family: sans-serif;
}
</style>
