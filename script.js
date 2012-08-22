d3.json('/visits', function (result)
  {
    d3.select('body').append('table').selectAll('tr')
        .data(result.rows)
      .enter().append('tr').selectAll('td')
        .data(function (d) { return d; })
      .enter().append('td')
        .text(function (d) { return d; });
  });
