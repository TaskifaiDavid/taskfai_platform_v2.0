import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { Sale } from '@/types'

interface SalesTableProps {
  sales: Sale[]
  title?: string
  description?: string
}

export function SalesTable({ sales, title = 'Sales Data', description }: SalesTableProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-EU', {
      style: 'currency',
      currency: 'EUR',
    }).format(value)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Date</TableHead>
              <TableHead>Reseller</TableHead>
              <TableHead>Product</TableHead>
              <TableHead>Channel</TableHead>
              <TableHead className="text-right">Units</TableHead>
              <TableHead className="text-right">Revenue</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sales.map((sale) => (
              <TableRow key={sale.sale_id}>
                <TableCell>{new Date(sale.date).toLocaleDateString()}</TableCell>
                <TableCell>{sale.reseller_name}</TableCell>
                <TableCell className="font-medium">{sale.product_name}</TableCell>
                <TableCell>
                  <span className="capitalize">{sale.channel}</span>
                </TableCell>
                <TableCell className="text-right">{sale.units_sold}</TableCell>
                <TableCell className="text-right font-medium">
                  {formatCurrency(sale.revenue_eur)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
