// CPU experiment only. Files must be derived and provenance-checked by the caller.
#define main antipodal_cube_checks
#include "cubes.cpp"
#undef main
#include <algorithm>
#include <bit>
#include <chrono>
#include <sys/resource.h>
#include <cstdint>
#include <fstream>
#include <stdexcept>
#include <string>
#include <type_traits>

constexpr std::size_t MAX_FACES=500000,MAX_VERTICES=1500000,MAX_POINTS=32;
template<typename T> std::vector<T> read_flat(const char* name,std::size_t stride,std::size_t maximum){
 static_assert(std::is_trivially_copyable_v<T>);
 if(std::endian::native!=std::endian::little)throw std::runtime_error("little-endian host required");
 std::ifstream f(name,std::ios::binary|std::ios::ate);if(!f)throw std::runtime_error("input open failed");auto end=f.tellg();
 if(end<=0||std::size_t(end)%(stride*sizeof(T))||std::size_t(end)/(stride*sizeof(T))>maximum)throw std::runtime_error("input size outside bounds");
 std::vector<T> x(std::size_t(end)/sizeof(T));f.seekg(0);if(!f.read(reinterpret_cast<char*>(x.data()),end))throw std::runtime_error("input read failed");return x;
}
// Detects near-edge positive ray hits only; absence of a flag is not a robustness proof.
unsigned near_edge_ray_hits(std::span<V const> verts,std::span<int const> faces,V p,V d){
 unsigned count=0;
 for(std::size_t i=0;i<faces.size();i+=3){
  V a=verts[faces[i]],e1=sub(verts[faces[i+1]],a),e2=sub(verts[faces[i+2]],a),h=cross3(d,e2);double det=dot3(e1,h);if(det==0)continue;
  V s=sub(p,a);double u=dot3(s,h)/det;if(u<0||u>1)continue;V q=cross3(s,e1);double v=dot3(d,q)/det;if(v<0||u+v>1)continue;double t=dot3(e2,q)/det;if(t<0)continue;
  if(std::min({u,v,1-u-v})<1e-10)++count;
 }
 return count;
}
// Flags queries close to triangle interiors or edges; tolerance is not an exact predicate.
unsigned near_surface_faces(std::span<V const> verts,std::span<int const> faces,V p,double eps){
 unsigned count=0;
 for(std::size_t i=0;i<faces.size();i+=3){
  V a=verts[faces[i]],b=verts[faces[i+1]],c=verts[faces[i+2]],e1=sub(b,a),e2=sub(c,a),n=cross3(e1,e2),w=sub(p,a);
  double nn=dot3(n,n);bool near=false;
  if(nn>0){double plane=dot3(w,n);if(std::abs(plane)<=eps*std::sqrt(nn)){
    V q=sub(w,{n.x*plane/nn,n.y*plane/nn,n.z*plane/nn});double d00=dot3(e1,e1),d01=dot3(e1,e2),d11=dot3(e2,e2),d20=dot3(q,e1),d21=dot3(q,e2),den=d00*d11-d01*d01;
    if(den>0){double u=(d11*d20-d01*d21)/den,v=(d00*d21-d01*d20)/den;near=u>=0&&v>=0&&u+v<=1;}
  }}
  for(auto edge:std::array<std::pair<V,V>,3>{{{a,b},{b,c},{c,a}}}){V d=sub(edge.second,edge.first),r=sub(p,edge.first);double dd=dot3(d,d),t=dd>0?std::clamp(dot3(r,d)/dd,0.0,1.0):0.0;V delta=sub(r,{d.x*t,d.y*t,d.z*t});if(norm3(delta)<=eps)near=true;}
  if(near)++count;
 }
 return count;
}
int main(int argc,char**argv){
 const auto started=std::chrono::steady_clock::now();
 try{
  if(argc!=4)throw std::runtime_error("usage: real_mesh positions.f64le faces.u32le points.f64le");
  auto xyz=read_flat<double>(argv[1],3,MAX_VERTICES);auto idx=read_flat<std::uint32_t>(argv[2],3,MAX_FACES);auto points=read_flat<double>(argv[3],3,MAX_POINTS);
  std::vector<antipodal::vec3<double>> vertices;std::vector<V> plain;vertices.reserve(xyz.size()/3);plain.reserve(xyz.size()/3);
  for(std::size_t i=0;i<xyz.size();i+=3){if(!std::isfinite(xyz[i])||!std::isfinite(xyz[i+1])||!std::isfinite(xyz[i+2]))throw std::runtime_error("nonfinite vertex");vertices.push_back({xyz[i],xyz[i+1],xyz[i+2]});plain.push_back({xyz[i],xyz[i+1],xyz[i+2]});}
  V low=plain.front(),high=plain.front();for(auto v:plain){low.x=std::min(low.x,v.x);low.y=std::min(low.y,v.y);low.z=std::min(low.z,v.z);high.x=std::max(high.x,v.x);high.y=std::max(high.y,v.y);high.z=std::max(high.z,v.z);}double surfaceEps=norm3(sub(high,low))*1e-10;
  std::vector<int> indices;indices.reserve(idx.size());for(auto value:idx){if(value>=vertices.size())throw std::runtime_error("index outside mesh");indices.push_back(int(value));}
  antipodal::NaiveIntersector<double> isect{vertices,indices};auto boundary=antipodal::build_boundary_segments<double>(vertices,indices);
  const std::array<antipodal::vec3<double>,2> dirs={antipodal::normalize(antipodal::vec3<double>{.31,.57,.76}),antipodal::normalize(antipodal::vec3<double>{.23,-.71,.66})};
  std::cout<<std::setprecision(17)<<"vertices="<<vertices.size()<<" triangles="<<indices.size()/3<<" boundary_segments="<<boundary.size()<<" surface_epsilon="<<surfaceEps<<" queries="<<points.size()/3<<'\n';
  for(std::size_t i=0;i<points.size();i+=3){V p{points[i],points[i+1],points[i+2]};if(!std::isfinite(p.x)||!std::isfinite(p.y)||!std::isfinite(p.z))throw std::runtime_error("nonfinite query");
   double direct=solid_angle_winding(vertices,indices,p);std::cout<<"point="<<i/3<<" direct="<<direct<<" near_surface_faces="<<near_surface_faces(plain,indices,p,surfaceEps);
   for(auto d:dirs){double value=antipodal::eval_gwnr_mesh_single<antipodal::NaiveIntersector<double>,double>({p.x,p.y,p.z},d,boundary,isect);unsigned near=near_edge_ray_hits(plain,indices,p,{d.x,d.y,d.z});std::cout<<" antipodal="<<value<<" abs_delta="<<std::abs(value-direct)<<" near_edge_hits="<<near;}
   std::cout<<'\n';
  }
  struct rusage usage{};if(getrusage(RUSAGE_SELF,&usage)!=0)throw std::runtime_error("getrusage failed");
  std::cout<<"elapsed_seconds="<<std::chrono::duration<double>(std::chrono::steady_clock::now()-started).count()<<" max_rss_kib="<<usage.ru_maxrss<<'\n';
  return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 2;}
}
