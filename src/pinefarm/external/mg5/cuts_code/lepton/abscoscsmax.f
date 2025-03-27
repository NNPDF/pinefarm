c     cut on the maximum of the absolute value of the cosine of the Collins-Soper angle of SFOS pairs
      do i=1,nexternal-1
        if (is_a_lm_reco(i) .or. is_a_lp_reco(i)) then
          do j=i+1,nexternal
            if (ipdg(i) .eq. -ipdg(j)) then
              if (is_a_lm_reco(i)) then
                zlep=i
                zalep=j
              else
                zlep=j
                zalep=i
              endif
              zenl=p(0,zlep)
              zptxl=p(1,zlep)
              zptyl=p(2,zlep)
              zpzl=p(3,zlep)
              zenal=p(0,zalep)
              zptxal=p(1,zalep)
              zptyal=p(2,zalep)
              zpzal=p(3,zalep)
c             implementation of first formula on page 6 of https://arxiv.org/abs/1710.05167
              zp1p=zenl+zpzl
              zp1m=zenl-zpzl
              zp2p=zenal+zpzal
              zp2m=zenal-zpzal
              zpzll=zpzl+zpzal
              zpt2ll=(zptxl+zptxal)*(zptxl+zptxal)+
     &               (zptyl+zptyal)*(zptyl+zptyal)
              zmll=sqrt((zenl+zenal)*(zenl+zenal)-(zpt2ll+zpzll*zpzll))
              zcoscs=(zp1p*zp2m-zp1m*zp2p)/
     &                    sqrt(zmll*zmll+zpt2ll)/zmll*sign(1d0,zpzll)

              if (abs(zcoscs) .gt. {}) then
                passcuts_leptons=.false.
                return
              endif
            endif
          enddo
        endif
      enddo
