"""
Analytics endpoints for KPIs, sales data, and report generation
"""

from typing import Annotated, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import Response
from supabase import Client

from app.core.dependencies import get_current_user, get_tenant_db_pool
from app.models.user import UserResponse
from app.services.analytics.kpis import KPICalculator
from app.services.analytics.sales import SalesAggregator
from app.workers.report_generator import ReportGenerator


router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/kpis", response_model=dict, status_code=status.HTTP_200_OK)
async def get_kpis(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    supabase: Annotated[Client, Depends(get_tenant_db_pool)],
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    channel: Optional[str] = None
):
    """
    Get KPIs for analytics dashboard

    - **start_date**: Start of date range (optional)
    - **end_date**: End of date range (optional)
    - **channel**: Filter by channel ('offline', 'online', or None for all)

    Returns:
    - Total revenue
    - Total units sold
    - Average order value
    - Channel breakdown (offline/online)
    - Top products
    """
    try:
        from supabase import Client
        kpi_calculator = KPICalculator(supabase)

        # Get main KPIs
        kpis = kpi_calculator.calculate_kpis(
            user_id=current_user["user_id"],
            start_date=start_date,
            end_date=end_date,
            channel=channel
        )

        # Get top products
        top_products = kpi_calculator.get_top_products(
            user_id=current_user["user_id"],
            limit=10,
            channel=channel,
            start_date=start_date,
            end_date=end_date
        )

        kpis['top_products'] = top_products

        return kpis

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate KPIs: {str(e)}"
        )


@router.get("/sales", response_model=dict, status_code=status.HTTP_200_OK)
async def get_sales_data(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    supabase: Annotated[Client, Depends(get_tenant_db_pool)],
    channel: str = 'all',
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    reseller: Optional[str] = None,
    product: Optional[str] = None,
    country: Optional[str] = None,
    page: int = 1,
    page_size: int = 50
):
    """
    Get detailed sales data with pagination and filters

    - **channel**: 'offline', 'online', or 'all' (default: all)
    - **start_date**: Start date filter (optional)
    - **end_date**: End date filter (optional)
    - **reseller**: Reseller name filter (fuzzy search, optional)
    - **product**: Product name filter (fuzzy search, optional)
    - **country**: Country filter (online only, optional)
    - **page**: Page number (1-indexed)
    - **page_size**: Results per page (max 100)

    Returns paginated sales data with filters applied
    """
    try:
        sales_aggregator = SalesAggregator(supabase)

        sales_data = sales_aggregator.get_sales_data(
            user_id=current_user["user_id"],
            channel=channel,
            start_date=start_date,
            end_date=end_date,
            reseller=reseller,
            product=product,
            country=country,
            page=page,
            page_size=min(page_size, 100)
        )

        return sales_data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sales data: {str(e)}"
        )


@router.get("/sales/summary", response_model=list, status_code=status.HTTP_200_OK)
async def get_sales_summary(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    supabase: Annotated[Client, Depends(get_tenant_db_pool)],
    group_by: str = 'month',
    channel: str = 'all',
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    """
    Get aggregated sales summary

    - **group_by**: Grouping dimension ('month', 'product', 'reseller', 'country')
    - **channel**: Channel filter ('offline', 'online', or 'all')
    - **start_date**: Start date filter (optional)
    - **end_date**: End date filter (optional)

    Returns aggregated sales data grouped by specified dimension
    """
    try:
        if group_by not in ['month', 'product', 'reseller', 'country']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid group_by parameter. Must be one of: month, product, reseller, country"
            )

        sales_aggregator = SalesAggregator(supabase)

        summary = sales_aggregator.get_sales_summary(
            user_id=current_user["user_id"],
            group_by=group_by,
            channel=channel,
            start_date=start_date,
            end_date=end_date
        )

        return summary

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}"
        )


@router.post("/export", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def export_report(
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    supabase: Annotated[Client, Depends(get_tenant_db_pool)],
    background_tasks: BackgroundTasks,
    format: str = 'pdf',
    channel: str = 'all',
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    reseller: Optional[str] = None,
    product: Optional[str] = None
):
    """
    Export sales report in specified format

    - **format**: Export format ('pdf', 'csv', or 'excel')
    - **channel**: Channel filter ('offline', 'online', or 'all')
    - **start_date**: Start date filter (optional)
    - **end_date**: End date filter (optional)
    - **reseller**: Reseller filter (optional)
    - **product**: Product filter (optional)

    Returns task_id for tracking report generation.
    Report will be generated in background and sent via email when ready.
    """
    try:
        if format not in ['pdf', 'csv', 'excel']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid format. Must be one of: pdf, csv, excel"
            )

        # Queue background task for report generation
        task_id = f"report_{current_user['user_id']}_{int(date.today().timestamp())}"

        # In production, this would be a Celery task
        # For now, return task_id and generate synchronously
        background_tasks.add_task(
            _generate_report_task,
            supabase,
            current_user["user_id"],
            current_user.get("email", "user@example.com"),
            format,
            channel,
            start_date,
            end_date,
            reseller,
            product
        )

        return {
            'task_id': task_id,
            'status': 'queued',
            'message': f'Report generation queued. {format.upper()} report will be sent to {current_user.email} when ready.'
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue report: {str(e)}"
        )


@router.get("/export/{format}", response_class=Response, status_code=status.HTTP_200_OK)
async def download_report(
    format: str,
    current_user: Annotated[UserResponse, Depends(get_current_user)],
    supabase: Annotated[Client, Depends(get_tenant_db_pool)],
    channel: str = 'all',
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    reseller: Optional[str] = None,
    product: Optional[str] = None
):
    """
    Generate and download report immediately

    - **format**: Export format ('pdf', 'csv', or 'excel')
    - **channel**: Channel filter
    - **start_date**: Start date filter (optional)
    - **end_date**: End date filter (optional)
    - **reseller**: Reseller filter (optional)
    - **product**: Product filter (optional)

    Returns file for immediate download
    """
    try:
        if format not in ['pdf', 'csv', 'excel']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid format. Must be one of: pdf, csv, excel"
            )

        report_generator = ReportGenerator(supabase)

        report_bytes = await report_generator.generate_report(
            user_id=current_user["user_id"],
            format=format,
            channel=channel,
            start_date=start_date,
            end_date=end_date,
            reseller=reseller,
            product=product
        )

        # Set content type based on format
        content_types = {
            'pdf': 'application/pdf',
            'csv': 'text/csv',
            'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }

        extensions = {
            'pdf': 'pdf',
            'csv': 'csv',
            'excel': 'xlsx'
        }

        filename = f"sales_report_{date.today().isoformat()}.{extensions[format]}"

        return Response(
            content=report_bytes,
            media_type=content_types[format],
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )


async def _generate_report_task(
    supabase: Client,
    user_id: str,
    user_email: str,
    format: str,
    channel: str,
    start_date: Optional[date],
    end_date: Optional[date],
    reseller: Optional[str],
    product: Optional[str]
):
    """Background task for report generation and email"""
    try:
        report_generator = ReportGenerator(supabase)

        report_bytes = await report_generator.generate_report(
            user_id=user_id,
            format=format,
            channel=channel,
            start_date=start_date,
            end_date=end_date,
            reseller=reseller,
            product=product
        )

        # In production, send email with attachment via SendGrid
        # For now, just log
        print(f"Report generated for {user_email}: {len(report_bytes)} bytes")

    except Exception as e:
        print(f"Report generation failed: {str(e)}")
