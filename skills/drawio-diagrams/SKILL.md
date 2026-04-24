---
name: drawio-diagrams
description: Generate Draw.io diagram files (.drawio). Use when creating diagrams, flowcharts, architecture docs, planning boards, HLD documents, or any visual documentation that needs to be opened in diagrams.net.
---

# Draw.io Diagram Generation

## File Structure

Draw.io files are XML with this structure:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" modified="2026-01-01T00:00:00.000Z" agent="Claude" version="24.0.0">
  <diagram name="Diagram Name" id="unique-id">
    <mxGraphModel dx="1400" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1400" pageHeight="1000">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- All content cells go here with parent="1" -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

## Cell Types

### Shape (Rectangle/Box)
```xml
<mxCell id="box1" value="Box Title" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="120" height="60" as="geometry" />
</mxCell>
```

### Text Only
```xml
<mxCell id="text1" value="Label Text" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;fontSize=14;fontStyle=1;" vertex="1" parent="1">
  <mxGeometry x="100" y="50" width="100" height="30" as="geometry" />
</mxCell>
```

### Arrow/Edge
```xml
<mxCell id="arrow1" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;html=1;strokeColor=#666666;strokeWidth=2;endArrow=classic;" edge="1" parent="1" source="box1" target="box2">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
```

### Swimlane/Container
```xml
<mxCell id="lane1" value="Section Title" style="swimlane;whiteSpace=wrap;html=1;startSize=25;" vertex="1" parent="1">
  <mxGeometry x="50" y="50" width="200" height="150" as="geometry" />
</mxCell>
<!-- Child cells use parent="lane1" -->
```

## Key Style Properties

| Property | Purpose | Example |
|----------|---------|---------|
| `fillColor` | Background color | `#dae8fc` |
| `strokeColor` | Border color | `#6c8ebf` |
| `strokeWidth` | Border thickness | `2` |
| `rounded` | Rounded corners | `1` (on) or `0` (off) |
| `arcSize` | Corner radius | `8` |
| `fontSize` | Text size | `12` |
| `fontStyle` | Text style | `0`=normal, `1`=bold, `2`=italic, `3`=bold+italic |
| `fontColor` | Text color | `#333333` |
| `align` | Horizontal align | `left`, `center`, `right` |
| `verticalAlign` | Vertical align | `top`, `middle`, `bottom` |
| `dashed` | Dashed line | `1` (on) |
| `dashPattern` | Dash pattern | `4 4` |

## Tips

- Use `html=1` in style to enable rich text (`<b>`, `<font>`)
- Use `&#xa;` for line breaks in `value` attribute
- Use `&lt;` and `&gt;` for angle brackets in text
- Give cells meaningful IDs (e.g., `login-box`, `api-arrow`)
- Set `parent="1"` for top-level cells, or parent ID for nested cells
- Use `source` and `target` attributes on edges to connect cells by ID
- Common page sizes: `1400x1000` (standard), `1800x1200` (large)
