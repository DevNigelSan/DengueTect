// ── DengueTect map layers (GIS) ──
// Real barangay boundaries, the Marikina River and health facilities from OpenStreetMap
// (app/static/geo/marikina.geojson). Barangay level only: no patient locations are ever mapped.

window.DTGIS = (function () {
  const style = document.createElement('style');
  style.textContent = `
    .gis-pin{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;
      background:#FFFFFF;border:2.5px solid #0D3B7A;box-shadow:0 2px 6px rgba(0,0,0,.35)}
    .gis-pin svg{display:block}
    .gis-pin.hospital{border-color:#B91C1C}
    .gis-label{font-family:'DM Sans',sans-serif;font-size:13px;font-weight:700;color:#FFFFFF;text-align:center;
      text-shadow:0 1px 3px rgba(0,0,0,.75);white-space:nowrap;pointer-events:none}
    .leaflet-control-layers{font-family:'Inter',sans-serif;font-size:13.5px;border-radius:10px!important}
    .leaflet-control-layers label{display:flex;align-items:center;gap:6px;margin:4px 0}
    .leaflet-control-layers input{width:16px;height:16px}
  `;
  document.head.appendChild(style);

  const crossIcon = color => `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="${color}" stroke-width="3.5" stroke-linecap="round"><line x1="12" y1="4" x2="12" y2="20"/><line x1="4" y1="12" x2="20" y2="12"/></svg>`;
  const fmt = n => Number(n).toLocaleString('en-US');

  // Adds boundaries, river, facilities and labels to a Leaflet map. Returns the barangay layers by name.
  function setup(map, geo) {
    const barangays = {};
    const brgyLayer = L.geoJSON(geo, {
      filter: f => f.properties.kind === 'barangay',
      style: { fillColor: '#94A3B8', fillOpacity: 0.6, color: '#FFFFFF', weight: 2.5 },
      onEachFeature: (f, layer) => { barangays[f.properties.name] = layer; layer.feature = f; }
    }).addTo(map);

    // Barangay names, at OpenStreetMap's label point (or the middle of the shape)
    geo.features.filter(f => f.properties.kind === 'barangay').forEach(f => {
      const pt = f.properties.label ? [f.properties.label[1], f.properties.label[0]]
                                    : barangays[f.properties.name].getBounds().getCenter();
      L.marker(pt, { interactive: false, keyboard: false,
        icon: L.divIcon({ className: '', html: `<div class="gis-label">${f.properties.name}</div>`,
                          iconSize: [90, 20], iconAnchor: [45, 10] }) }).addTo(map);
    });

    const river = L.geoJSON(geo, {
      filter: f => f.properties.kind === 'river',
      style: { color: '#2563EB', weight: 4, opacity: 0.8 }
    }).bindTooltip('Marikina River', { sticky: true }).addTo(map);

    const facilities = L.geoJSON(geo, {
      filter: f => f.properties.kind === 'facility',
      pointToLayer: (f, latlng) => {
        const hospital = f.properties.type === 'Hospital';
        return L.marker(latlng, {
          title: f.properties.name,
          icon: L.divIcon({ className: '', iconSize: [28, 28], iconAnchor: [14, 14],
            html: `<div class="gis-pin${hospital ? ' hospital' : ''}">${crossIcon(hospital ? '#B91C1C' : '#0D3B7A')}</div>` })
        }).bindPopup(`<div style="font-family:'Inter',sans-serif;min-width:170px;">
            <div style="font-family:'DM Sans',sans-serif;font-size:14px;font-weight:700;color:#0D3B7A;margin-bottom:4px;">${f.properties.name}</div>
            <div style="font-size:13px;color:#475569;">${f.properties.type}</div></div>`);
      }
    }).addTo(map);

    L.control.layers(null, {
      'Marikina River': river,
      'Health facilities': facilities
    }, { collapsed: false, position: 'topright' }).addTo(map);

    if (Object.keys(barangays).length) map.fitBounds(brgyLayer.getBounds(), { padding: [24, 24] });
    map.attributionControl.addAttribution('Boundaries &amp; facilities © OpenStreetMap contributors (ODbL)');
    return barangays;
  }

  // "Population (2024): 54,134" for a barangay's popup
  function population(layer) {
    const p = layer && layer.feature && layer.feature.properties;
    return p && p.population ? `Population (${p.population_year}): ${fmt(p.population)}` : '';
  }

  return { setup, population };
})();
