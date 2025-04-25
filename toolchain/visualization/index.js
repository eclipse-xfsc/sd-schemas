import d3 from 'd3';
import jsonldVis from 'jsonld-vis';
jsonldVis(d3);

d3.json(process.env.FILE, (err, data) => {
    if (err) return console.warn(err);
    d3.jsonldVis(data, '#graph', { w: 800, h: 600, maxLabelWidth: 250 });
});
