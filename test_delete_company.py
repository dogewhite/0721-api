from database import engine, SessionLocal
from models import Company, Project, Position, PositionCandidate
from sqlalchemy import text

def test_delete_company():
    """测试删除公司功能"""
    session = SessionLocal()
    try:
        # 首先查看当前数据
        companies = session.query(Company).all()
        print(f"当前公司数量: {len(companies)}")
        
        projects = session.query(Project).all()
        print(f"当前项目数量: {len(projects)}")
        
        positions = session.query(Position).all()
        print(f"当前职位数量: {len(positions)}")
        
        candidates = session.query(PositionCandidate).all()
        print(f"当前候选人关联数量: {len(candidates)}")
        
        # 找一个有数据的公司ID来测试
        if companies:
            test_company = companies[0]
            print(f"\n准备删除公司: {test_company.name} (ID: {test_company.id})")
            
            # 查看这个公司的相关数据
            company_projects = session.query(Project).filter(Project.company_id == test_company.id).all()
            print(f"该公司的项目数量: {len(company_projects)}")
            
            # 模拟删除逻辑（不真正删除）
            for project in company_projects:
                project_positions = session.query(Position).filter(Position.project_id == project.id).all()
                print(f"项目 '{project.name}' 的职位数量: {len(project_positions)}")
                
                project_candidates = session.query(PositionCandidate).filter(PositionCandidate.project_id == project.id).all()
                print(f"项目 '{project.name}' 的候选人关联数量: {len(project_candidates)}")
        
        print("\n测试完成 - 没有实际删除数据")
        
    except Exception as e:
        print(f"测试失败: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    test_delete_company() 