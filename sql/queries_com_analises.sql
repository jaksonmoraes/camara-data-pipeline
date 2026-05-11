-- 1: Média de gastos por parlamentar (Normalizado por Partido)
select
    round((sum(ddes.valor_liquido) / count(distinct ddes.deputado_id))::numeric, 2) as media_por_parlamentar
from 
    deputados_trusted.deputados_despesas_trusted ddes;


-- 2: Ranking de Escolaridade vs. Volume de Gastos
select 
    det.escolaridade,
    count(distinct det.id) as total_parlamentares,
    round(sum(des.valor_liquido)::numeric, 2) as gasto_total
from 
    deputados_trusted.deputados_detalhes_trusted det
join 
    deputados_trusted.deputados_despesas_trusted des ON det.id = des.deputado_id
group by 
    det.escolaridade
order by 
    gasto_total desc;


-- 3: Total de gastos por partido
with 
	d1 as(
select
	distinct(count(dr.id)) as total_ids, 
	dr.sigla_partido as partido 
from deputados_trusted.deputados_trusted dr group by 2
),
	d2 as(

select 
	distinct(ddes.deputado_id) as id, 
	ddes.ano, 
	round(sum(ddes.valor_documento)::numeric, 2) as doc, 
	round(sum(ddes.valor_liquido)::numeric, 2) as liq
from deputados_trusted.deputados_despesas_trusted ddes
where ano = 2025
group by 1,2
order by 1
)

select
	d1.total_ids, d1.partido, round(sum(d2.doc)::numeric, 2)
from deputados_trusted.deputados_trusted dt 
inner join d2 d2 on dt.id = d2.id
inner join d1 d1 on dt.sigla_partido = d1.partido
group by 1,2;